#!/bin/bash
set -u
cd -- "$(dirname -- "$0")"
python3 -m backend.quest_link
result=$?
read -r -p 'Zum Schließen Enter drücken.'
exit "$result"
