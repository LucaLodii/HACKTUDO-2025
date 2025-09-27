@echo off
REM Git cleanup script to resolve permission issues
echo Cleaning up git repository...

REM Run git garbage collection
echo Running git garbage collection...
git gc --prune=now

REM Clean up any loose objects
echo Cleaning up loose objects...
git prune

REM Verify git status
echo Checking git status...
git status

echo Git cleanup completed!
pause
