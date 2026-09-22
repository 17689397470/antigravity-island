@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在后台启动 Antigravity 灵动岛...

where pythonw >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw capsule_gui.py
) else (
    start "" python capsule_gui.py
)
echo 启动成功。
