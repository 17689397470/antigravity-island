@echo off
chcp 65001 >nul
echo ========================================================
echo   Antigravity Island - 一键便携单文件 EXE 打包构建工具
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/5] 检查并准备构建环境...
python -c "import PyInstaller" >nul 2>nul
if %errorlevel% neq 0 (
    echo [提示] 未检测到 PyInstaller，正在自动安装...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [错误] PyInstaller 安装失败，请检查网络或 pip 配置！
        pause
        exit /b 1
    )
)

echo [2/5] 生成 256px 多层级矢量 Windows 图标 (app.ico)...
python generate_icon.py
if not exist "assets\app.ico" (
    echo [错误] 未能生成 assets\app.ico 图标！
    pause
    exit /b 1
)

echo [3/5] 执行深度瘦身编译 (PyInstaller Single-File)...
pyinstaller --clean AntigravityIsland.spec
if %errorlevel% neq 0 (
    echo [错误] PyInstaller 构建失败，请查看上方错误输出！
    pause
    exit /b 1
)

if not exist "dist\AntigravityIsland.exe" (
    echo [错误] 未在 dist 目录下找到生成的 AntigravityIsland.exe！
    pause
    exit /b 1
)

echo.
echo [4/5] 计算产物 SHA256 哈希指纹...
powershell -NoProfile -Command ^
    "$exe = 'dist\AntigravityIsland.exe'; " ^
    "$hash = (Get-FileHash -Algorithm SHA256 $exe).Hash; " ^
    "$size = (Get-Item $exe).Length / 1MB; " ^
    "Write-Host ('产物文件: ' + $exe); " ^
    "Write-Host ('文件大小: ' + [Math]::Round($size, 2) + ' MB'); " ^
    "Write-Host ('SHA-256 : ' + $hash); " ^
    "Set-Content -Path 'dist\SHA256SUMS.txt' -Value ($hash + '  AntigravityIsland.exe');"

echo.
echo [5/5] 打包生成便携 Release ZIP 资产包...
powershell -NoProfile -Command ^
    "$zip = 'dist\AntigravityIsland-v2.0.0-windows-x64.zip'; " ^
    "if (Test-Path $zip) { Remove-Item -Force $zip }; " ^
    "Compress-Archive -Path 'dist\AntigravityIsland.exe', 'README.md', 'README_EN.md', 'LICENSE' -DestinationPath $zip; " ^
    "if (Test-Path $zip) { " ^
    "    $zsize = (Get-Item $zip).Length / 1MB; " ^
    "    Write-Host ('发布资产: ' + $zip); " ^
    "    Write-Host ('压缩大小: ' + [Math]::Round($zsize, 2) + ' MB'); " ^
    "}"

echo.
echo ========================================================
echo [成功] 独立便携免安装版本构建完成！
echo 产物位置:
echo   - 单文件主程序: dist\AntigravityIsland.exe
echo   - 校验和指纹  : dist\SHA256SUMS.txt
echo   - 发布压缩包  : dist\AntigravityIsland-v2.0.0-windows-x64.zip
echo ========================================================
echo.
pause
