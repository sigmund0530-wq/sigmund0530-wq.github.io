#!/bin/sh
set -e
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
(sleep 2; python3 -m webbrowser http://127.0.0.1:8766 >/dev/null 2>&1) &
python3 server.py
