@echo off
REM sofIA Cloud Run Deployment Script - Copy Version
REM This script copies the project to a temp location without .git

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Copy Version - No Git Issues
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    pause
    exit /b 1
)

echo Step 1: Creating clean copy of project...

REM Create temp directory
set TEMP_DIR=C:\Users\Asus\AppData\Local\Temp\sofia_deploy_temp
if exist "%TEMP_DIR%" (
    echo Cleaning old temp directory...
    rmdir /s /q "%TEMP_DIR%" 2>nul
)

echo Creating temporary project copy...
mkdir "%TEMP_DIR%" 2>nul

REM Copy all files except .git
echo Copying project files (excluding .git)...
xcopy /E /I /H /Y /EXCLUDE:git_exclude.txt . "%TEMP_DIR%" >nul 2>&1

if errorlevel 1 (
    echo Creating git exclude file...
    echo .git\ > git_exclude.txt
    echo .git\* >> git_exclude.txt
    echo .git\objects\ >> git_exclude.txt
    echo .git\refs\ >> git_exclude.txt
    echo .git\hooks\ >> git_exclude.txt
    echo .git\info\ >> git_exclude.txt
    echo .git\logs\ >> git_exclude.txt
    
    echo Retrying copy...
    xcopy /E /I /H /Y /EXCLUDE:git_exclude.txt . "%TEMP_DIR%" >nul 2>&1
)

echo Step 2: Deploying from clean copy...

REM Change to temp directory and deploy
cd /d "%TEMP_DIR%"

REM Deploy to Cloud Run
"C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" deploy cloud_run --project graceful-mile-473404-d1 --region us-central1 --with_ui .

if errorlevel 1 (
    echo.
    echo ========================================
    echo    DEPLOYMENT FAILED!
    echo ========================================
    echo.
    echo The deployment failed from the clean copy.
    echo This might be a different issue now.
) else (
    echo.
    echo ========================================
    echo    DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your sofIA application has been deployed to Google Cloud Run!
)

echo Step 3: Cleaning up...

REM Return to original directory
cd /d "%~dp0"

REM Clean up temp directory
if exist "%TEMP_DIR%" (
    echo Cleaning up temporary files...
    rmdir /s /q "%TEMP_DIR%" 2>nul
)

REM Clean up exclude file
if exist "git_exclude.txt" (
    del "git_exclude.txt" 2>nul
)

echo.
echo Process completed!
pause
