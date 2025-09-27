@echo off
REM sofIA Cloud Run Deployment Script (Batch version)
REM This script handles permission issues during deployment

echo Starting sofIA Cloud Run deployment...

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo Error: Please run this script from the project root directory
    exit /b 1
)

REM Clean up any existing temporary files
echo Cleaning up temporary files...
if exist "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" (
    rmdir /s /q "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" 2>nul
    echo Temporary files cleaned up successfully
)

REM Ensure we have the latest ADK version
echo Checking ADK version...
"C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" --version
if errorlevel 1 (
    echo Error: ADK not found. Please ensure Google ADK is installed and in your PATH
    exit /b 1
)

REM Deploy to Cloud Run
echo Starting deployment...
"C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" deploy cloud_run --project graceful-mile-473404-d1 --region us-central1 --with_ui .

if errorlevel 1 (
    echo.
    echo Deployment failed. Try the following manual steps:
    echo 1. Close any file explorers or IDEs that might be accessing the project directory
    echo 2. Run 'git gc --prune=now' to clean up git objects
    echo 3. Try running the deployment command manually
    echo.
    echo Manual command:
    echo "C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" deploy cloud_run --project graceful-mile-473404-d1 --region us-central1 --with_ui .
    pause
    exit /b 1
) else (
    echo Deployment completed successfully!
)

pause
