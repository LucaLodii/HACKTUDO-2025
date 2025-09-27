@echo off
REM sofIA Cloud Run Deployment Script - Final Solution
REM This script completely avoids git permission issues

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Final Solution - No Git Issues
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Creating completely clean project copy...

REM Create temp directory
set TEMP_DIR=C:\Users\Asus\AppData\Local\Temp\sofia_clean_deploy
if exist "%TEMP_DIR%" (
    echo Cleaning old temp directory...
    rmdir /s /q "%TEMP_DIR%" 2>nul
)

echo Creating clean project copy...
mkdir "%TEMP_DIR%" 2>nul

REM Copy only the essential files (no .git, no cache, no temp files)
echo Copying essential project files...

REM Copy main Python files
copy "*.py" "%TEMP_DIR%\" >nul 2>&1
copy "pyproject.toml" "%TEMP_DIR%\" >nul 2>&1
copy "README.md" "%TEMP_DIR%\" >nul 2>&1
copy "Dockerfile" "%TEMP_DIR%\" >nul 2>&1
copy "docker-compose.yml" "%TEMP_DIR%\" >nul 2>&1
copy "nginx.conf" "%TEMP_DIR%\" >nul 2>&1

REM Copy directories (excluding .git)
if exist "orchestrator" (
    echo Copying orchestrator directory...
    xcopy /E /I /H /Y "orchestrator" "%TEMP_DIR%\orchestrator" >nul 2>&1
)

if exist "sofIA" (
    echo Copying sofIA directory...
    xcopy /E /I /H /Y "sofIA" "%TEMP_DIR%\sofIA" >nul 2>&1
)

if exist "tests" (
    echo Copying tests directory...
    xcopy /E /I /H /Y "tests" "%TEMP_DIR%\tests" >nul 2>&1
)

if exist "whatsapp-bridge" (
    echo Copying whatsapp-bridge directory...
    xcopy /E /I /H /Y "whatsapp-bridge" "%TEMP_DIR%\whatsapp-bridge" >nul 2>&1
)

REM Copy .adkignore
copy ".adkignore" "%TEMP_DIR%\" >nul 2>&1

echo Step 2: Deploying from clean copy...

REM Change to temp directory
cd /d "%TEMP_DIR%"

echo Current directory: %CD%
echo Files in directory:
dir /b

echo.
echo Starting deployment...

REM Deploy to Cloud Run
"C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" deploy cloud_run --project graceful-mile-473404-d1 --region us-central1 --with_ui .

if errorlevel 1 (
    echo.
    echo ========================================
    echo    DEPLOYMENT FAILED!
    echo ========================================
    echo.
    echo The deployment failed. This could be due to:
    echo 1. Google Cloud authentication issues
    echo 2. Network connectivity problems
    echo 3. Project configuration issues
    echo.
    echo Please check:
    echo 1. Are you logged into Google Cloud? (gcloud auth login)
    echo 2. Is the project ID correct? (graceful-mile-473404-d1)
    echo 3. Do you have Cloud Run permissions?
    echo.
    echo Try running: gcloud auth login
    echo Then run this script again.
) else (
    echo.
    echo ========================================
    echo    DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your sofIA application has been deployed to Google Cloud Run!
    echo.
    echo Next steps:
    echo 1. Check Google Cloud Console: https://console.cloud.google.com/run?project=graceful-mile-473404-d1
    echo 2. Look for your sofIA service
    echo 3. Click on it to get the public URL
    echo 4. Test your application
)

echo Step 3: Cleaning up...

REM Return to original directory
cd /d "%~dp0"

REM Clean up temp directory
if exist "%TEMP_DIR%" (
    echo Cleaning up temporary files...
    rmdir /s /q "%TEMP_DIR%" 2>nul
)

echo.
echo Process completed!
pause
