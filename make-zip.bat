@echo off
rem Builds the MART zip for the work laptop. Double-click it in the repo folder:
rem fetches the latest version (git pull), builds dist\MART-<version>.zip,
rem tests it, and shows it in Explorer.  make-zip.bat --no-pull skips the pull.
rem This file is for the PC with the repo; it is not part of the zip.
setlocal
cd /d "%~dp0"
title MART - build zip

call "%~dp0mart\find-python.cmd"
if not defined PY (
  echo.
  echo   Python 3.12 or newer was not found on this computer. The zip was NOT built.
  echo.
  if not defined MART_NO_PAUSE pause
  exit /b 1
)

rem Everything else happens in Python, and this MUST stay the last line: the
rem git pull may rewrite this very file, and cmd reads batch files as it goes.
"%PY%" -X utf8 tools\build_zip.py --pull --verify --open --pause %* & exit /b
