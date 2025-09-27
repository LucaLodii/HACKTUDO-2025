@echo off
REM Check Google Cloud authentication status

echo ========================================
echo    Checking Google Cloud Authentication
echo ========================================
echo.

echo Checking if you're logged into Google Cloud...

REM Check if gcloud is installed
where gcloud >nul 2>&1
if errorlevel 1 (
    echo ERROR: Google Cloud CLI (gcloud) is not installed or not in PATH
    echo.
    echo Please install Google Cloud CLI from:
    echo https://cloud.google.com/sdk/docs/install
    echo.
    pause
    exit /b 1
)

echo Google Cloud CLI found. Checking authentication...

REM Check current authentication
gcloud auth list

echo.
echo Checking current project...
gcloud config get-value project

echo.
echo ========================================
echo    Authentication Status
echo ========================================
echo.

REM Check if user is authenticated
gcloud auth list --filter=status:ACTIVE --format="value(account)" >nul 2>&1
if errorlevel 1 (
    echo ❌ NOT AUTHENTICATED
    echo.
    echo You need to log in to Google Cloud first.
    echo Run: gcloud auth login
    echo.
) else (
    echo ✅ AUTHENTICATED
    echo.
    echo You are logged into Google Cloud.
    echo.
)

echo Current project: 
gcloud config get-value project

echo.
echo ========================================
echo    Next Steps
echo ========================================
echo.

REM Check if project is set correctly
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set CURRENT_PROJECT=%%i

if "%CURRENT_PROJECT%"=="graceful-mile-473404-d1" (
    echo ✅ Project is set correctly: %CURRENT_PROJECT%
    echo.
    echo You can now run: deploy-final.bat
) else (
    echo ❌ Project is not set correctly
    echo Current project: %CURRENT_PROJECT%
    echo Expected project: graceful-mile-473404-d1
    echo.
    echo To fix this, run:
    echo gcloud config set project graceful-mile-473404-d1
    echo.
)

echo.
pause
