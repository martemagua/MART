@echo off
rem MART - Martin's Awesome Renewal Tool
rem Double-click to start. Optional: MART.bat check | backup | restore <file>
setlocal
cd /d "%~dp0"
title MART

rem --- Find a real Python 3.10 or newer --------------------------------------
rem Every candidate is test-run before it is used, so the Microsoft Store
rem placeholder ("Python was not found ...") is skipped automatically.
set "PY="
rem 1. The work laptop's Python 3.12
call :try "%ProgramFiles%\Python312\python.exe"
rem 2. The py launcher (python.org installer and the Python install manager)
if not defined PY for /f "delims=" %%E in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do call :try "%%E"
rem 3. The usual install folders, newest first
if not defined PY for /f "delims=" %%D in ('dir /b /ad /o-n "%LOCALAPPDATA%\Programs\Python\Python3*" 2^>nul') do call :try "%LOCALAPPDATA%\Programs\Python\%%D\python.exe"
if not defined PY for /f "delims=" %%D in ('dir /b /ad /o-n "%LOCALAPPDATA%\Python\pythoncore-3*" 2^>nul') do call :try "%LOCALAPPDATA%\Python\%%D\python.exe"
if not defined PY for /f "delims=" %%D in ('dir /b /ad /o-n "%ProgramFiles%\Python3*" 2^>nul') do call :try "%ProgramFiles%\%%D\python.exe"
rem 4. Whatever "python" means on PATH
if not defined PY for /f "delims=" %%P in ('where python 2^>nul') do call :try "%%P"

if not defined PY (
  echo.
  echo   MART needs Python 3.12 or newer, and none was found on this computer.
  echo   Install it from https://www.python.org/downloads/ and start MART.bat again.
  echo.
  if not defined MART_NO_PAUSE pause
  exit /b 1
)

"%PY%" -X utf8 -m mart %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" if not defined MART_NO_PAUSE (
  echo.
  pause
)
exit /b %RC%

rem --- :try <path>  use it if it exists and really is Python 3.10+ -----------
:try
if defined PY exit /b 0
if not exist "%~1" exit /b 1
"%~1" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul || exit /b 1
set "PY=%~1"
exit /b 0
