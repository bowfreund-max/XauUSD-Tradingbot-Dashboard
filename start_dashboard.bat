@echo off
cd /d "%~dp0"
py -3 bridge.py
if errorlevel 1 (
  echo.
  echo Python could not start. Install Python 3 and try again.
  pause
)
