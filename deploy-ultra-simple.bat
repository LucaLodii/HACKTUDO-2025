@echo off
REM Ultra simple deployment using basic Dockerfile

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Ultra Simple Version
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Using simple Dockerfile...

REM Copy simple Dockerfile
copy Dockerfile.simple Dockerfile

echo Step 2: Building and deploying...

REM Build and deploy
gcloud run deploy sofia --source . --platform managed --region us-central1 --allow-unauthenticated --port 8080

if errorlevel 1 (
    echo.
    echo ========================================
    echo    DEPLOYMENT FAILED!
    echo ========================================
    echo.
    echo The deployment failed. Let's try a different approach.
    echo.
    echo Trying with a minimal Python app...
    
    REM Create a minimal test app
    echo Creating minimal test app...
    (
    echo from fastapi import FastAPI
    echo.
    echo app = FastAPI^(title="sofIA Test"^)
    echo.
    echo @app.get^("/"^)
    echo def read_root^(^):
    echo     return {"message": "sofIA is running!", "status": "success"}
    echo.
    echo @app.get^("/health"^)
    echo def health_check^(^):
    echo     return {"status": "healthy"}
    ) > test_app.py
    
    echo Deploying minimal test app...
    gcloud run deploy sofia-test --source . --platform managed --region us-central1 --allow-unauthenticated --port 8080
    
    if errorlevel 1 (
        echo.
        echo Both deployments failed. Please check:
        echo 1. Google Cloud authentication
        echo 2. Project permissions
        echo 3. Build logs in Google Cloud Console
    ) else (
        echo.
        echo ========================================
        echo    MINIMAL APP DEPLOYED!
        echo ========================================
        echo.
        echo A minimal test version of sofIA has been deployed.
        echo This proves the deployment process works.
        echo.
        echo Getting the service URL...
        gcloud run services describe sofia-test --region=us-central1 --format="value(status.url)"
    )
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
