@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object CommandLine -like '*capsule_gui.py*' | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>nul
exit
