"""Regression tests against real loopback HTTP/TLS connections.

The TLS fixture trusts its temporary certificate explicitly; verification is
never disabled. No external service or user credential is used.
"""

import base64
import http.client
import os
from pathlib import Path
import re
import select
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from backend.server import Application, JarvisServer


class TrackingServer(JarvisServer):
    def __init__(self, *args, **kwargs):
        self.active = 0
        self.condition = threading.Condition()
        super().__init__(*args, **kwargs)

    def process_request_thread(self, request, client_address):
        with self.condition:
            self.active += 1
            self.condition.notify_all()
        try:
            super().process_request_thread(request, client_address)
        finally:
            with self.condition:
                self.active -= 1
                self.condition.notify_all()

    def wait_for_active(self, count):
        with self.condition:
            return self.condition.wait_for(lambda: self.active == count, timeout=3)


class ConnectionLimitsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.server = TrackingServer(('127.0.0.1', 0), Application(self.temp.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.clients = []

    def tearDown(self):
        for connection in self.clients:
            connection.close()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def stalled_headers(self):
        connection = socket.create_connection(self.server.server_address, timeout=3)
        self.clients.append(connection)
        connection.sendall(b'GET /api/session HTTP/1.1\r\n')
        return connection

    def session_status(self):
        client = http.client.HTTPConnection(*self.server.server_address, timeout=2)
        try:
            client.request('GET', '/api/session')
            response = client.getresponse()
            response.read()
            return response.status
        finally:
            client.close()

    def test_worker_limit_closes_overflow_and_recovers(self):
        for _ in range(24):
            self.stalled_headers()
        self.assertTrue(self.server.wait_for_active(24), 'Expected stalled requests to reach the worker limit')
        overflow = socket.create_connection(self.server.server_address, timeout=2)
        try:
            overflow.settimeout(2)
            try:
                data = overflow.recv(1)
            except ConnectionResetError:
                data = b''
            self.assertEqual(data, b'', 'Overflow must be closed instead of starting another worker')
        finally:
            overflow.close()
        self.assertEqual(self.server.active, 24)
        for connection in self.clients:
            connection.close()
        self.clients.clear()
        self.assertTrue(self.server.wait_for_active(0), 'Closed clients must release all worker slots')
        self.assertEqual(self.session_status(), 200)

    def test_incomplete_headers_expire_while_other_requests_work(self):
        stalled = self.stalled_headers()
        self.assertTrue(self.server.wait_for_active(1))
        self.assertEqual(self.session_status(), 200)
        started = time.monotonic()
        stalled.settimeout(12)
        self.assertEqual(stalled.recv(1), b'', 'Slow header reads must expire without needing a completed request')
        self.assertLess(time.monotonic() - started, 12)


@unittest.skipUnless(shutil.which('openssl'), 'TLS regression fixture requires the existing openssl command')
class TLSHandshakeTests(unittest.TestCase):
    def test_silent_tls_client_does_not_block_authenticated_request(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cert, key = root / 'cert.pem', root / 'key.pem'
            configuration = root / 'openssl.cnf'
            configuration.write_text(
                '[req]\ndistinguished_name=dn\nx509_extensions=v3_req\nprompt=no\n'
                '[dn]\nCN=localhost\n[v3_req]\nsubjectAltName=IP:127.0.0.1\n', encoding='utf-8')
            subprocess.run([
                shutil.which('openssl'), 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                '-keyout', str(key), '-out', str(cert), '-days', '1',
                '-config', str(configuration),
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            # Exercise the actual CLI listener construction, including deferred
            # handshakes, instead of reconstructing a separate test TLS server.
            process = subprocess.Popen([
                sys.executable, '-m', 'backend', '--port', '0', '--data-dir', str(root / 'data'),
                '--cert', str(cert), '--key', str(key),
            ], cwd=Path(__file__).resolve().parent.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env={**os.environ, 'JARVIS_ACCESS_PASSWORD': 'fixture-only-tls-password'})
            idle = None
            try:
                self.assertTrue(select.select([process.stdout], [], [], 5)[0], 'Server did not report readiness')
                line = process.stdout.readline()
                match = re.search(r'Port ([0-9]+)', line)
                self.assertIsNotNone(match, 'Server failed to start its TLS listener')
                port = int(match.group(1))
                idle = socket.create_connection(('127.0.0.1', port), timeout=2)
                # This peer intentionally never starts a TLS handshake. A
                # listener that handshakes in accept() would block the next peer.
                context = ssl.create_default_context(cafile=str(cert))
                client = http.client.HTTPSConnection('127.0.0.1', port, context=context, timeout=3)
                try:
                    credentials = base64.b64encode(b'jarvis:fixture-only-tls-password').decode('ascii')
                    client.request('GET', '/api/session', headers={'Authorization': 'Basic ' + credentials})
                    response = client.getresponse()
                    self.assertEqual(response.status, 200)
                    self.assertIn(b'"token"', response.read())
                finally:
                    client.close()
            finally:
                if idle is not None:
                    idle.close()
                process.terminate()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate(timeout=5)


if __name__ == '__main__':
    unittest.main()
