@echo off
cd /d "%~dp0"
REM 若未构建前端，会尝试连 http://127.0.0.1:5173/ ，请先 npm run dev
python -m backend.main
pause
