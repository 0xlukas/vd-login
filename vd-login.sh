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
source venv/bin/activate
python3 login.py
