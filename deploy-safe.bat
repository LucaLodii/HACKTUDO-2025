@echo off
REM sofIA Cloud Run Deployment Script - Safe Version
REM This script temporarily removes .git folder to avoid permission issues

echo Starting sofIA Cloud Run deployment (Safe Mode)...

REM Check if we're in the correct directory
if not exist "pyproject.toml" (
    echo Error: Please run this script from the project root directory
    pause
    exit /b 1
)

REM Check if .git folder exists
if not exist ".git" (
    echo Warning: .git folder not found. This might not be a git repository.
    echo Continuing with deployment...
    goto :deploy
)

REM Create backup of .git folder
echo Creating backup of .git folder...
if exist ".git_backup" (
    rmdir /s /q ".git_backup" 2>nul
)
move ".git" ".git_backup" >nul 2>&1
if errorlevel 1 (
    echo Error: Could not backup .git folder. Please close any programs using this directory.
    pause
    exit /b 1
)
echo .git folder backed up successfully

:deploy
REM Clean up any existing temporary files
echo Cleaning up temporary files...
if exist "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" (
    rmdir /s /q "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" 2>nul
    echo Temporary files cleaned up successfully
)

REM Deploy to Cloud Run
echo Starting deployment...
"C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" deploy cloud_run --project graceful-mile-473404-d1 --region us-central1 --with_ui .

if errorlevel 1 (
    echo.
    echo Deployment failed!
    goto :restore
) else (
    echo Deployment completed successfully!
)

:restore
REM Restore .git folder
if exist ".git_backup" (
    echo Restoring .git folder...
    if exist ".git" (
        rmdir /s /q ".git" 2>nul
    )
    move ".git_backup" ".git" >nul 2>&1
    if errorlevel 1 (
        echo Warning: Could not restore .git folder. Please restore it manually from .git_backup
    ) else (
        echo .git folder restored successfully
    )
)

echo.
echo Process completed!
pause
