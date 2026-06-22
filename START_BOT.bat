@echo off
echo Starting Stock Market Bot Dashboard...
echo.
echo Your browser will open in a few seconds.
echo DO NOT close this black window — it keeps the dashboard running.
echo.
cd /d "%~dp0"
streamlit run dashboard.py
pause
