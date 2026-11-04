@echo off
rem MART - Martin's Awesome Renewal Tool
rem Double-click to start. Optional: MART.bat check | backup | restore <file>
setlocal
cd /d "%~dp0"
title MART

set "PY="
if exist "%ProgramFiles%\Python312\python.exe" set "PY=%ProgramFiles%\Python312\python.exe"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul') do if not defined PY set "PY=%%P"
if not defined PY (
  echo.
  echo   Python 3.12 was not found on this computer. MART needs it to run.
  echo.
  pause
  exit /b 1
)

"%PY%" -X utf8 -m mart %*
if errorlevel 1 (
  echo.
  pause
)
endlocal
