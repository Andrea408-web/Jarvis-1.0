#!/bin/bash
# Ausschließlich vom Benutzer ausdrücklich gestartete Zertifikatseinrichtung.
set -eu
cd -- "$(dirname -- "$0")"
echo 'Startet das offizielle Zertifikatsskript einer passenden python.org-Installation.'
echo 'Dieses Skript kann Pythons Zertifikatspaket installieren oder aktualisieren.'
exec python3 -m backend --repair-certificates
