#!/bin/bash
set -eu
cd -- "$(dirname -- "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python 3.10 oder neuer fehlt. Es wird nichts automatisch installiert.'
  read -r -p 'Zum Schließen Enter drücken.'
  exit 1
fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else "Python 3.10 oder neuer wird benötigt.")'
python3 -m backend --easy-local
