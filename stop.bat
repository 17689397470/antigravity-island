@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "Get-Process -Name 'AntigravityIsland' -ErrorAction SilentlyContinue | Stop-Process -Force; Get-CimInstance Win32_Process -Filter \"CommandLine LIKE '%%capsule_gui.py%%'\" -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>nul
exit
