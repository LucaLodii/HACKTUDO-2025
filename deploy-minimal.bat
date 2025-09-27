@echo off
REM Deploy minimal sofIA app

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Minimal Working Version
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "app_simple.py" (
    echo ERROR: app_simple.py not found
    pause
    exit /b 1
)

echo Step 1: Using minimal Dockerfile...

REM Copy minimal Dockerfile
copy Dockerfile.minimal Dockerfile

echo Step 2: Building and deploying...

REM Build and deploy
gcloud run deploy sofia --source . --platform managed --region us-central1 --allow-unauthenticated --port 8080

if errorlevel 1 (
    echo.
    echo ========================================
    echo    DEPLOYMENT FAILED!
    echo ========================================
    echo.
    echo The deployment failed. Let's check what went wrong.
    echo.
    echo Recent builds:
    gcloud builds list --limit=2
    echo.
    echo Please check the build logs in Google Cloud Console:
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
    echo.
    echo Test endpoints:
    echo - Root: [URL]/
    echo - Health: [URL]/health
    echo - WhatsApp: [URL]/process-whatsapp-message
)

echo.
pause
