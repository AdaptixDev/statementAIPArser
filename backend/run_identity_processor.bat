@echo off
REM Run the identity document processor

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or higher.
    exit /b 1
)

REM Check if a PDF file was provided
if "%~1"=="" (
    echo Usage: run_identity_processor.bat [pdf_file] [document_type]
    echo.
    echo document_type can be:
    echo   - driving_license (default)
    echo   - passport
    exit /b 1
)

REM Set the document type (default to driving_license if not provided)
set DOC_TYPE=driving_license
if not "%~2"=="" (
    set DOC_TYPE=%~2
)

REM Run the processor
echo Running identity document processor for %DOC_TYPE%...
python process_identity_document.py --pdf "%~1" --type %DOC_TYPE%

if %ERRORLEVEL% neq 0 (
    echo Failed to process the document.
    exit /b 1
)

echo.
echo Document processing complete.
echo. 