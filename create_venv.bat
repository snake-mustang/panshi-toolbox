@echo off
cd /d "%~dp0"
echo 正在创建虚拟环境 .venv ...
python -m venv .venv
if errorlevel 1 (
    echo 创建失败，请确认已安装 Python。
    pause
    exit /b 1
)
echo 正在安装依赖...
.venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
echo 完成。运行: .venv\Scripts\python.exe run_webview.py
echo 打包带 OCR 时请用 Python 3.11/3.12 并执行: pip install -r requirements-ocr.txt
pause
