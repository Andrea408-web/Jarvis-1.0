#!/bin/bash
# Keine Installation und keine automatischen Berechtigungsänderungen.
set -eu
cd -- "$(dirname -- "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3.10 oder neuer wird benötigt. Bitte zuerst die Anleitung README.md lesen.'
  read -r -p 'Zum Schließen die Eingabetaste drücken.'
  exit 1
fi
exec python3 -m backend --open-browser
