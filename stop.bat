@echo off
chcp 65001 >nul
echo Stopping Antigravity Context Capsule...
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*capsule_gui.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Stopped.
