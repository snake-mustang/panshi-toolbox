@echo off
cd /d "%~dp0"
echo [1/2] 打包前端...
cd frontend
call npm run build
if errorlevel 1 ( echo 前端打包失败 & pause & exit /b 1 )
cd ..
echo [2/2] 启动工具箱...
python run_webview.py
pause
