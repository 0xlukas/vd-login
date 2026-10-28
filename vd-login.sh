#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title VD Login
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🖥️
# @raycast.packageName VDLogin

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# venv/ is not in git, so a fresh clone (or a venv whose Python was removed)
# needs setting up. Also reinstall when requirements.txt changes.
if [ ! -x venv/bin/python ] || [ ! -f venv/.installed ] || [ requirements.txt -nt venv/.installed ]; then
  [ -x venv/bin/python ] || python3 -m venv --clear venv || { echo "Could not create venv"; exit 1; }
  venv/bin/python -m pip install -q -r requirements.txt \
    && venv/bin/python -m playwright install chromium \
    && touch venv/.installed \
    || { echo "Dependency install failed"; exit 1; }
fi

venv/bin/python login.py
