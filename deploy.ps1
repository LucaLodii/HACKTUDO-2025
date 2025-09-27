# sofIA Cloud Run Deployment Script
# This script handles permission issues during deployment

Write-Host "Starting sofIA Cloud Run deployment..." -ForegroundColor Green

# Check if we're in the correct directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Error "Please run this script from the project root directory"
    exit 1
}

# Clean up any existing temporary files
Write-Host "Cleaning up temporary files..." -ForegroundColor Yellow
if (Test-Path "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src") {
    try {
        Remove-Item -Path "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Temporary files cleaned up successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Could not clean up all temporary files: $($_.Exception.Message)"
    }
}

# Ensure we have the latest ADK version
Write-Host "Checking ADK version..." -ForegroundColor Yellow
try {
    $adkVersion = & "C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe" --version
    Write-Host "ADK Version: $adkVersion" -ForegroundColor Green
} catch {
    Write-Error "ADK not found. Please ensure Google ADK is installed and in your PATH"
    exit 1
}

# Deploy to Cloud Run with retry logic
$maxRetries = 3
$retryCount = 0

do {
    $retryCount++
    Write-Host "Deployment attempt $retryCount of $maxRetries..." -ForegroundColor Yellow
    
    try {
        # Run the deployment command
        $deployCommand = @(
            "C:\Users\Asus\AppData\Roaming\Python\Python313\Scripts\adk.exe"
            "deploy"
            "cloud_run"
            "--project"
            "graceful-mile-473404-d1"
            "--region"
            "us-central1"
            "--with_ui"
            "."
        )
        
        & $deployCommand[0] $deployCommand[1..($deployCommand.Length-1)]
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Deployment completed successfully!" -ForegroundColor Green
            break
        } else {
            Write-Warning "Deployment failed with exit code $LASTEXITCODE"
        }
    } catch {
        Write-Warning "Deployment attempt $retryCount failed: $($_.Exception.Message)"
    }
    
    if ($retryCount -lt $maxRetries) {
        Write-Host "Waiting 10 seconds before retry..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        
        # Clean up temp files before retry
        if (Test-Path "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src") {
            try {
                Remove-Item -Path "C:\Users\Asus\AppData\Local\Temp\cloud_run_deploy_src" -Recurse -Force -ErrorAction SilentlyContinue
            } catch {
                Write-Warning "Could not clean up temporary files before retry"
            }
        }
    }
} while ($retryCount -lt $maxRetries)

if ($retryCount -eq $maxRetries) {
    Write-Error "Deployment failed after $maxRetries attempts"
    Write-Host "Try the following manual steps:" -ForegroundColor Yellow
    Write-Host "1. Close any file explorers or IDEs that might be accessing the project directory" -ForegroundColor Yellow
    Write-Host "2. Run 'git gc --prune=now' to clean up git objects" -ForegroundColor Yellow
    Write-Host "3. Try running the deployment command manually" -ForegroundColor Yellow
    exit 1
}

Write-Host "Deployment process completed!" -ForegroundColor Green
