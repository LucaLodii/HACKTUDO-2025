@echo off
REM Deploy sofIA to Cloud Run in background

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Background Mode
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Starting deployment in background...
echo This will take a few minutes. You can close this window.
echo.

REM Start the build in background
start /B gcloud builds submit --config cloudbuild.yaml . > build.log 2>&1

echo Build started in background!
echo.
echo To check progress:
echo 1. Open build.log file to see real-time logs
echo 2. Or check Google Cloud Console:
echo    https://console.cloud.google.com/cloud-build/builds?project=graceful-mile-473404-d1
echo.
echo To check if deployment completed:
echo 1. Run: gcloud run services list --region=us-central1
echo 2. Or run: check-deployment-status.bat
echo.

pause
