@echo off
REM Simple Cloud Run deployment using gcloud

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Simple gcloud method
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Configuring Docker for Google Cloud...

REM Configure Docker for Google Cloud
gcloud auth configure-docker

echo Step 2: Building and pushing image...

REM Build and push in one command
gcloud builds submit --tag gcr.io/graceful-mile-473404-d1/sofia:latest .

if errorlevel 1 (
    echo.
    echo ========================================
    echo    BUILD FAILED!
    echo ========================================
    echo.
    echo The build failed. This could be due to:
    echo 1. Missing dependencies in pyproject.toml
    echo 2. Build errors in the code
    echo 3. Network issues
    echo.
    echo Check the build logs above for details.
    pause
    exit /b 1
)

echo Step 3: Deploying to Cloud Run...

REM Deploy to Cloud Run
gcloud run deploy sofia --image gcr.io/graceful-mile-473404-d1/sofia:latest --platform managed --region us-central1 --allow-unauthenticated --port 8080

if errorlevel 1 (
    echo.
    echo ========================================
    echo    DEPLOYMENT FAILED!
    echo ========================================
    echo.
    echo The deployment failed. Please check:
    echo 1. Are you authenticated? (gcloud auth login)
    echo 2. Do you have Cloud Run permissions?
    echo 3. Is the project ID correct?
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
