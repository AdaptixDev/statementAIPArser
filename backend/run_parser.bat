@echo off
echo Running statement parser...
echo PDF: %1
echo Output: %3
echo Use Gemini: %5

REM Set the Python path to include the parent directory
set PYTHONPATH=%~dp0..

REM Add Poppler binaries to the PATH
set PATH=%PATH%;%~dp0..\poppler\Release-24.08.0-0\poppler-24.08.0\Library\bin

REM Debug: Print environment variables
echo PYTHONPATH: %PYTHONPATH%
echo PATH: %PATH%
echo Current directory: %CD%

REM Try to use Python from PATH
python %~dp0\src\main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo Python from PATH failed, trying with python3...
    python3 %~dp0\src\main.py %*
    if %ERRORLEVEL% NEQ 0 (
        echo Python3 failed too. Please make sure Python is installed and in your PATH.
        echo Trying with the standalone script...
        python %~dp0\process_statement.py %*
    )
) 