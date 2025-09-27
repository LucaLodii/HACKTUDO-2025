@echo off
REM Check deployment status

echo ========================================
echo    Checking sofIA Deployment Status
echo ========================================
echo.

echo Checking Cloud Run services...
gcloud run services list --region=us-central1

echo.
echo Checking recent builds...
gcloud builds list --limit=3

echo.
echo ========================================
echo    Next Steps
echo ========================================
echo.

REM Check if sofia service exists
gcloud run services describe sofia --region=us-central1 --format="value(status.url)" >nul 2>&1
if errorlevel 1 (
    echo ❌ sofIA service not found
    echo.
    echo The deployment might still be running or failed.
    echo Check the build logs for details.
    echo.
    echo To check build logs:
    echo 1. Go to: https://console.cloud.google.com/cloud-build/builds?project=graceful-mile-473404-d1
    echo 2. Click on the most recent build
    echo 3. Check the logs for errors
) else (
    echo ✅ sofIA service found!
    echo.
    echo Getting service URL...
    for /f "tokens=*" %%i in ('gcloud run services describe sofia --region=us-central1 --format="value(status.url)"') do set SERVICE_URL=%%i
    echo.
    echo Your sofIA application is running at:
    echo %SERVICE_URL%
    echo.
    echo You can now test your application!
)

echo.
pause
