@echo off
REM sofIA Cloud Run Deployment Script - Simple Version
REM This script deploys without touching .git folder

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Simple Version - No Git Issues
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Cleaning temporary files...

REM Clean up any existing deployment temp files
if exist "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" (
    echo Cleaning old deployment files...
    rmdir /s /q "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" 2>nul
)

REM Clean up Python cache files
echo Cleaning Python cache files...
if exist "__pycache__" (
    rmdir /s /q "__pycache__" 2>nul
)
if exist "*.pyc" (
    del /q "*.pyc" 2>nul
)

echo Step 2: Deploying to Cloud Run...
echo.

REM Deploy to Cloud Run
"C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" deploy cloud_run --project graceful-mile-473404-d1 --region us-central1 --with_ui .

REM Check if deployment was successful (ignore cleanup errors)
if errorlevel 1 (
    echo.
    echo ========================================
    echo    CHECKING DEPLOYMENT STATUS...
    echo ========================================
    echo.
    echo The ADK command completed with an error code, but this might just be
    echo a cleanup issue. Let's check if the deployment actually succeeded.
    echo.
    echo Please check your Google Cloud Console to see if the service was deployed:
    echo https://console.cloud.google.com/run?project=graceful-mile-473404-d1
    echo.
    echo If you see your sofIA service there, the deployment was successful!
    echo The error was just from cleaning up temporary files.
) else (
    echo.
    echo ========================================
    echo    DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your sofIA application has been deployed to Google Cloud Run!
    echo You can now access it through the provided URL.
)

echo.
echo ========================================
echo    NEXT STEPS:
echo ========================================
echo 1. Check Google Cloud Console: https://console.cloud.google.com/run?project=graceful-mile-473404-d1
echo 2. Look for your sofIA service in the list
echo 3. Click on the service to get the public URL
echo 4. Test your application using the provided URL
echo.

echo.
pause
