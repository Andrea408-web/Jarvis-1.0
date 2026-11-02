#!/bin/bash
set -eu
cd -- "$(dirname -- "$0")"
exec python3 -m backend --start-small-ai
