@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First-time setup is needed. Follow START_HERE.md, then run this launcher again.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run app.py
pause
