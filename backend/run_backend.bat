@echo off
cd /d "%~dp0"
echo [Leviathan_Eye] Backend starting from: %CD%
echo [Leviathan_Eye] Python: & python --version
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000
echo.
echo [Leviathan_Eye] Server stopped. Press any key to close.
pause
