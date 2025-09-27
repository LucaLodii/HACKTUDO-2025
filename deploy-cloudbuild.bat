@echo off
REM Deploy using Google Cloud Build without local Docker

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Cloud Build Only (No Local Docker)
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Creating cloudbuild.yaml...

REM Create cloudbuild.yaml for Google Cloud Build
echo Creating cloudbuild.yaml configuration...
(
echo # Cloud Build configuration for sofIA
echo steps:
echo   # Build the container image
echo   - name: 'gcr.io/cloud-builders/docker'
echo     args: ['build', '-t', 'gcr.io/graceful-mile-473404-d1/sofia:$BUILD_ID', '.']
echo   # Push the container image to Container Registry
echo   - name: 'gcr.io/cloud-builders/docker'
echo     args: ['push', 'gcr.io/graceful-mile-473404-d1/sofia:$BUILD_ID']
echo   # Deploy container image to Cloud Run
echo   - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
echo     entrypoint: gcloud
echo     args:
echo       - 'run'
echo       - 'deploy'
echo       - 'sofia'
echo       - '--image'
echo       - 'gcr.io/graceful-mile-473404-d1/sofia:$BUILD_ID'
echo       - '--region'
echo       - 'us-central1'
echo       - '--platform'
echo       - 'managed'
echo       - '--allow-unauthenticated'
echo       - '--port'
echo       - '8080'
echo images:
echo   - 'gcr.io/graceful-mile-473404-d1/sofia:$BUILD_ID'
) > cloudbuild.yaml

echo cloudbuild.yaml created successfully!

echo Step 2: Starting Cloud Build...

REM Submit the build
gcloud builds submit --config cloudbuild.yaml .

if errorlevel 1 (
    echo.
    echo ========================================
    echo    BUILD/DEPLOY FAILED!
    echo ========================================
    echo.
    echo The build or deployment failed. This could be due to:
    echo 1. Missing dependencies in pyproject.toml
    echo 2. Build errors in the code
    echo 3. Network issues
    echo 4. Cloud Run permissions
    echo.
    echo Check the build logs above for details.
    echo.
    echo You can also check the build status at:
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

echo Step 3: Cleaning up...

REM Clean up cloudbuild.yaml
if exist "cloudbuild.yaml" (
    del "cloudbuild.yaml"
    echo Cleaned up cloudbuild.yaml
)

echo.
echo Process completed!
pause
