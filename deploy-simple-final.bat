@echo off
REM Simple final deployment

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Simple Final Version
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Building and deploying...

REM Build and deploy in one command
gcloud run deploy sofia --source . --platform managed --region us-central1 --allow-unauthenticated --port 8080

if errorlevel 1 (
    echo.
    echo ========================================
    echo    DEPLOYMENT FAILED!
    echo ========================================
    echo.
    echo The deployment failed. This could be due to:
    echo 1. Build errors in the code
    echo 2. Missing dependencies
    echo 3. Network issues
    echo 4. Cloud Run permissions
    echo.
    echo Check the error messages above for details.
    echo.
    echo You can also check the build logs at:
    echo https://console.cloud.google.com/cloud-build/builds?project=graceful-mile-473404-d1
) else (
    echo.
    echo ========================================
    echo    DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your sofIA application has been deployed to Cloud Run!
    echo.
    echo Getting the service URL...
    gcloud run services describe sofia --region=us-central1 --format="value(status.url)"
    echo.
    echo You can now access your application at the URL above!
)

echo.
pause
