#!/usr/bin/env bash
# Mac / Linux launcher. First time: chmod +x start.sh
cd "$(dirname "$0")"
python3 -m pip install --quiet playwright
python3 muj_feedback_gui.py
