@echo off
cd /d "%~dp0"
REM 本地运行（与打包后的 exe 同一套界面）。先执行 create_venv.bat 或 pip install -r requirements.txt
python run_webview.py
pause
