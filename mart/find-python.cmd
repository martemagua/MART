@rem Finds a real Python 3.10 or newer and puts its path in PY (empty if none).
@rem Shared by MART.bat and make-zip.bat, so the search exists only once.
@rem No setlocal on purpose: PY has to reach the script that called this one.
@rem
@rem Every candidate is test-run before it is used, so the Microsoft Store
@rem placeholder ("Python was not found ...") is skipped automatically.
@echo off
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
exit /b 0

rem --- :try <path>  use it if it exists and really is Python 3.10+ -----------
:try
if defined PY exit /b 0
if not exist "%~1" exit /b 1
"%~1" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul || exit /b 1
set "PY=%~1"
exit /b 0
