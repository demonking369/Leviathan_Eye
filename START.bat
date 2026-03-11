@echo off
setlocal EnableDelayedExpansion
title Leviathan_Eye - Global Intelligence Dashboard

cls
echo.
echo  ================================================================
echo   Leviathan_Eye  --  Global Intelligence Dashboard  //  Cyber Edition
echo  ================================================================
echo.

REM -- Check Python ----------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERR] Python not found. Download from https://python.org
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK]  %%v found

REM -- Install requirements (silent) -----------------------------------------
echo  [..] Installing / verifying Python dependencies...
python -m pip install -r "%~dp0backend\requirements.txt" -q --disable-pip-version-check
if errorlevel 1 (
    echo  [ERR] pip install failed. Try running as Administrator.
    pause & exit /b 1
)
echo  [OK]  Dependencies verified

REM -- AI Mode Selection ------------------------------------------------------
echo.
echo  +----------------------------------------------------------+
echo  ^|  SELECT AI MODE                                          ^|
echo  ^|                                                          ^|
echo  ^|   1  Ollama  (local LLM - private, free, recommended)   ^|
echo  ^|   2  API Key (OpenAI / Groq / Mistral compatible)        ^|
echo  ^|   3  No AI   (map + feeds + cyber layer only)            ^|
echo  +----------------------------------------------------------+
echo.
set /p AI_CHOICE="  Your choice [1/2/3]: "

if "!AI_CHOICE!"=="2" goto :api_key_mode
if "!AI_CHOICE!"=="3" goto :no_ai_mode
goto :ollama_mode

REM ---------------------------------------------------------------------------
:ollama_mode
echo.
echo  [Ollama Mode]
ollama --version >nul 2>&1
if errorlevel 1 (
    echo  [ERR] Ollama not found.
    echo        Download: https://ollama.com/download
    pause & exit /b 1
)
echo  [OK]  Ollama found

REM Start Ollama only if not already running
ollama list >nul 2>&1
if errorlevel 1 (
    echo  [..] Starting Ollama server...
    start /min "Ollama Server" ollama serve
    timeout /t 4 /nobreak >nul
) else (
    echo  [OK]  Ollama already running
)

REM -- Build numbered model list (filter header and error lines) -------------
echo.
echo  +----------------------------------------------------------+
echo  ^|  INSTALLED MODELS                                        ^|
echo  +----------------------------------------------------------+
echo.

set MODEL_COUNT=0
for /f "tokens=1" %%m in ('ollama list 2^>nul ^| findstr /v /i /c:"NAME" /c:"failed" /c:"error" /c:"handle"') do (
    set /a MODEL_COUNT+=1
    set "MODEL_!MODEL_COUNT!=%%m"
    echo    [!MODEL_COUNT!]  %%m
)
echo.

if !MODEL_COUNT! equ 0 (
    echo  [WARN] No models found.
    echo.
    set /p PULL_MODEL="  Pull a model (e.g. llama3:latest) or leave blank to skip: "
    if not "!PULL_MODEL!"=="" (
        echo  [..] Pulling !PULL_MODEL! ...
        ollama pull !PULL_MODEL!
        if errorlevel 1 ( echo  [ERR] Pull failed. & pause & exit /b 1 )
        set SELECTED_MODEL=!PULL_MODEL!
        set TOOL_MODE=text
        goto :detect_tools
    ) else (
        echo  [WARN] No model. Switching to No AI mode.
        goto :no_ai_mode
    )
)

echo  Enter the number shown, or type a full model name.
echo.
set /p MODEL_INPUT="  Model: "

set SELECTED_MODEL=!MODEL_INPUT!
for /l %%i in (1,1,!MODEL_COUNT!) do (
    if "!MODEL_INPUT!"=="%%i" set SELECTED_MODEL=!MODEL_%%i!
)

if "!SELECTED_MODEL!"=="" ( echo  [ERR] No model selected. & pause & exit /b 1 )
echo  [OK]  Model: !SELECTED_MODEL!

:detect_tools
set TOOL_MODE=text
for %%m in (mistral llama3.1 llama3.2 llama3.3 qwen2.5 qwen2 command-r hermes functionary nexusraven mixtral) do (
    echo !SELECTED_MODEL! | findstr /i "%%m" >nul 2>&1 && set TOOL_MODE=native
)
echo  [OK]  Tool mode: !TOOL_MODE!

:write_config_ollama
echo  [..] Saving config...
(
echo {
echo   "mode": "ollama",
echo   "key": "",
echo   "url": "",
echo   "model": "",
echo   "ollama_model": "!SELECTED_MODEL!",
echo   "tool_mode": "!TOOL_MODE!"
echo }
) > "%~dp0backend\config.json"
goto :launch

REM ---------------------------------------------------------------------------
:api_key_mode
echo.
echo  [API Key Mode]
echo.
set /p API_URL="  API Base URL [https://api.openai.com/v1]: "
if "!API_URL!"=="" set API_URL=https://api.openai.com/v1
set /p API_KEY="  API Key: "
if "!API_KEY!"=="" ( echo  [ERR] API key cannot be empty. & pause & exit /b 1 )
set /p API_MODEL="  Model [gpt-4o-mini]: "
if "!API_MODEL!"=="" set API_MODEL=gpt-4o-mini
echo  [OK]  URL: !API_URL!  Model: !API_MODEL!
(
echo {
echo   "mode": "openai",
echo   "key": "!API_KEY!",
echo   "url": "!API_URL!",
echo   "model": "!API_MODEL!",
echo   "ollama_model": "",
echo   "tool_mode": "text"
echo }
) > "%~dp0backend\config.json"
goto :launch

REM ---------------------------------------------------------------------------
:no_ai_mode
echo.
echo  [No AI Mode - Map + Satellite + Cyber only]
(
echo {
echo   "mode": "none",
echo   "key": "",
echo   "url": "",
echo   "model": "",
echo   "ollama_model": "",
echo   "tool_mode": "text"
echo }
) > "%~dp0backend\config.json"

REM ---------------------------------------------------------------------------
:launch
echo.
echo  +----------------------------------------------------------+
echo  ^|  LAUNCHING Leviathan_Eye                                     ^|
echo  +----------------------------------------------------------+
echo.
echo  [..] Starting backend - a new window will open.
echo  [..] If the backend window shows errors, read them before closing.
echo.

REM Use run_backend.bat to avoid all quoting / path issues
start "Leviathan_Eye Backend" "%~dp0backend\run_backend.bat"

echo  [..] Waiting for server to start...
timeout /t 6 /nobreak >nul

echo  [..] Opening browser...
start http://localhost:8000

echo.
echo  ================================================================
echo   Leviathan_Eye is running at http://localhost:8000
echo   The "Leviathan_Eye Backend" window must stay open.
echo   Close that window to stop the server.
echo  ================================================================
echo.
pause
