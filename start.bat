@echo off
cd /d "%~dp0"
where pythonw >nul 2>nul
if %ERRORLEVEL% equ 0 (
    start "" pythonw "%~dp0capsule_gui.py"
) else (
    start "" python "%~dp0capsule_gui.py"
)
