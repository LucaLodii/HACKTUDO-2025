@echo off
REM Deploy using gcloud directly instead of ADK

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Using gcloud directly
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Building Docker image...

REM Build the Docker image
echo Building Docker image...
docker build -t gcr.io/graceful-mile-473404-d1/sofia:latest .

if errorlevel 1 (
    echo ERROR: Docker build failed
    echo Make sure Docker is running and you have Docker installed
    pause
    exit /b 1
)

echo Step 2: Pushing to Google Container Registry...

REM Push to GCR
echo Pushing image to Google Container Registry...
docker push gcr.io/graceful-mile-473404-d1/sofia:latest

if errorlevel 1 (
    echo ERROR: Docker push failed
    echo Make sure you're authenticated with Google Cloud
    echo Try running: gcloud auth configure-docker
    pause
    exit /b 1
)

echo Step 3: Deploying to Cloud Run...

REM Deploy to Cloud Run
echo Deploying to Cloud Run...
gcloud run deploy sofia --image gcr.io/graceful-mile-473404-d1/sofia:latest --platform managed --region us-central1 --allow-unauthenticated

if errorlevel 1 (
    echo.
    echo ========================================
    echo    DEPLOYMENT FAILED!
    echo ========================================
    echo.
    echo The deployment failed. Please check:
    echo 1. Are you authenticated? (gcloud auth login)
    echo 2. Is Docker running?
    echo 3. Do you have Cloud Run permissions?
) else (
    echo.
    echo ========================================
    echo    DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your sofIA application has been deployed to Cloud Run!
    echo.
    echo To get the URL, run:
    echo gcloud run services describe sofia --region=us-central1 --format="value(status.url)"
)

echo.
pause
