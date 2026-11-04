@echo off
rem MART - Martin's Awesome Renewal Tool
rem Double-click to start. Optional: MART.bat check | backup | restore <file>
setlocal
cd /d "%~dp0"
title MART

call "%~dp0mart\find-python.cmd"
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
