@echo off
REM Check if sofIA deployment was successful

echo ========================================
echo    Checking sofIA Deployment Status
echo ========================================
echo.

echo Opening Google Cloud Console to check deployment...
echo.

echo Please check the following:
echo 1. Go to: https://console.cloud.google.com/run?project=graceful-mile-473404-d1
echo 2. Look for a service named "sofia" or "hackatudo-2025"
echo 3. If you see it, click on the service name
echo 4. Copy the URL provided (it should end with .run.app)
echo.

echo If you see your service listed, the deployment was SUCCESSFUL!
echo The error you saw was just from cleaning up temporary files.
echo.

echo To test your application:
echo 1. Copy the URL from Google Cloud Console
echo 2. Open it in your browser
echo 3. You should see your sofIA application running
echo.

echo If you don't see any service listed, the deployment failed.
echo In that case, try running deploy-simple.bat again.
echo.

pause
