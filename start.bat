@echo off
cd /d "%~dp0"
echo Checking requirements...
python -m pip install --quiet playwright
python muj_feedback_gui.py
if errorlevel 1 pause
