@echo off
chcp 65001 >nul
echo ========================================================
echo   Antigravity Island - 一键同步推送到 GitHub 与 Gitee
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] 暂存所有代码变更...
git add .

echo.
set /p commit_msg="请输入 Commit 描述 (直接回车默认: feat: update antigravity-island): "
if "%commit_msg%"=="" set commit_msg=feat: update antigravity-island

git commit -m "%commit_msg%"

echo.
echo [2/3] 正在推送到 GitHub (origin main)...
git push -u origin main
if %errorlevel% neq 0 (
    echo [警告] 推送到 GitHub 遇到问题，可能需要登录或检查网络连接。
) else (
    echo [成功] GitHub 推送完成！
)

echo.
echo [3/3] 正在推送到 Gitee (gitee main)...
git -c http.proxy="" push -u gitee main
if %errorlevel% neq 0 (
    echo [警告] 推送到 Gitee 遇到问题，可能需要登录或检查网络连接。
) else (
    echo [成功] Gitee 推送完成！
)

echo.
echo ========================================================
echo 同步操作结束。
echo ========================================================
pause
