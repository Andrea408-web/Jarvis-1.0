#!/bin/bash
# Uses the existing, configured macOS Jarvis installation; no downloads.
set -u
cd -- "$(dirname -- "$0")"
if [ "$(uname -s)" != 'Darwin' ]; then
  echo 'Dieser Starter benötigt die bereits eingerichtete macOS-Version von Jarvis.'
  echo 'Er installiert keine KI-Laufzeit auf einem neuen Linux-Mini-PC.'
  read -r -p 'Zum Schließen Enter drücken.'
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3 fehlt. Verwende den Interpreter deiner vorhandenen Jarvis-Installation.'
  read -r -p 'Zum Schließen Enter drücken.'
  exit 1
fi
if [ ! -f backend/__main__.py ]; then
  echo 'Diese Datei muss im bisherigen Jarvis-Ordner neben dem Ordner backend liegen.'
  echo 'Die einzelne Datei auf einem USB-Stick enthält weder Jarvis noch die lokale KI.'
  read -r -p 'Zum Schließen Enter drücken.'
  exit 1
fi
printf '%s\n' 'JARVIS TV startet mit der vorhandenen lokalen KI.' 'Verbinde den Mac per HDMI mit dem Fernseher oder nutze die private TV-Kopplung.' 'Dieses Terminal geöffnet lassen. Beenden mit Strg+C.'
python3 -m backend --easy-local --open-tv
result=$?
if [ "$result" -ne 0 ]; then
  printf '%s\n' 'Der Start ist fehlgeschlagen. Die Meldung darüber enthält den nächsten Schritt.' 'Wenn Jarvis schon läuft, beende zuerst die alte Terminal-Instanz mit Strg+C.'
fi
read -r -p 'Zum Schließen Enter drücken.'
exit "$result"
