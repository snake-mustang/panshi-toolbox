@echo off
cd /d "%~dp0"
REM 打包前请用 Python 3.11 或 3.12 并已执行: pip install -r requirements.txt -r requirements-ocr.txt
echo 正在检查 PyInstaller...
python -m pip install pyinstaller -q
echo.
echo 正在打包（目录模式，启动快）...
python -m PyInstaller --noconfirm --windowed --name "盘古开发工具箱" ^
  run_webview.py ^
  --add-data "static;static" ^
  --hidden-import=webview ^
  --hidden-import=backend.api_webview ^
  --hidden-import=backend.ocr_engine ^
  --hidden-import=numpy
if errorlevel 1 (
    echo 打包失败。
    pause
    exit /b 1
)
echo.
echo 打包完成。输出目录: dist\盘古开发工具箱\
echo 将 dist\盘古开发工具箱 整个文件夹发给用户即可。
pause
