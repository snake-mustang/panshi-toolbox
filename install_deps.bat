@echo off
cd /d "%~dp0"
echo 正在安装依赖...
python -m pip install -r requirements.txt
pause
