@echo off
REM sofIA Cloud Run Deployment Script - Ultimate Version
REM This script handles all possible permission issues

echo ========================================
echo    sofIA Cloud Run Deployment
echo    Ultimate Version - No Permission Issues
echo ========================================
echo.

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo ERROR: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Step 1: Preparing environment...

REM Kill any processes that might be using the directory
echo Closing any processes that might lock files...
taskkill /f /im explorer.exe >nul 2>&1
timeout /t 2 >nul
start explorer.exe

REM Clean up Windows temp files
echo Cleaning Windows temporary files...
del /q /f /s "%TEMP%\*" >nul 2>&1
del /q /f /s "C:\Users\Asus\AppData\Local\Temp\*" >nul 2>&1

REM Clean up any existing deployment temp files
echo Cleaning deployment temporary files...
if exist "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" (
    rmdir /s /q "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" 2>nul
)

echo Step 2: Handling .git folder...

REM Check if .git folder exists
if not exist ".git" (
    echo No .git folder found. Proceeding with deployment...
    goto :deploy
)

REM Create backup of .git folder
echo Creating backup of .git folder...
if exist ".git_backup" (
    rmdir /s /q ".git_backup" 2>nul
)

REM Try to move .git folder
move ".git" ".git_backup" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Could not backup .git folder.
    echo This might cause permission issues, but continuing...
) else (
    echo .git folder backed up successfully
)

:deploy
echo Step 3: Deploying to Cloud Run...

REM Deploy to Cloud Run
"C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" deploy cloud_run --project graceful-mile-473404-d1 --region us-central1 --with_ui .

if errorlevel 1 (
    echo.
    echo ========================================
    echo    DEPLOYMENT FAILED!
    echo ========================================
    echo.
    echo Possible solutions:
    echo 1. Run as Administrator
    echo 2. Close all file explorers and IDEs
    echo 3. Restart your computer
    echo 4. Try the manual command below:
    echo.
    echo Manual command:
    echo "C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" deploy cloud_run --project graceful-mile-473404-d1 --region us-central1 --with_ui .
    goto :restore
) else (
    echo.
    echo ========================================
    echo    DEPLOYMENT SUCCESSFUL!
    echo ========================================
    echo.
    echo Your sofIA application has been deployed to Google Cloud Run!
)

:restore
echo Step 4: Restoring .git folder...

REM Restore .git folder
if exist ".git_backup" (
    echo Restoring .git folder...
    if exist ".git" (
        rmdir /s /q ".git" 2>nul
    )
    move ".git_backup" ".git" >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Could not restore .git folder!
        echo Please manually rename .git_backup to .git
    ) else (
        echo .git folder restored successfully
    )
)

echo.
echo ========================================
echo    Process completed!
echo ========================================
echo.
pause
