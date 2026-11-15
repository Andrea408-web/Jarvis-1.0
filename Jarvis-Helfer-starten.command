#!/bin/bash
set -u
cd -- "$(dirname -- "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3.10 oder neuer wird benötigt. Es wird nichts automatisch installiert.'
  read -r -p 'Zum Schließen Enter drücken.'
  exit 1
fi
python3 -m backend.companion_window
result=$?
read -r -p 'Zum Schließen Enter drücken.'
exit "$result"
