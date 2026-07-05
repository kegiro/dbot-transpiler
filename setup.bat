@echo off
echo ===========================================
echo   DBot Windows CLI Auto-Setup
echo ===========================================
echo.

:: 1. Create the dbot.bat script in the current directory
echo [1/3] Creating dbot.bat launcher...
(
echo @echo off
echo python "%%~dp0main.py" %%*
) > dbot.bat
echo Done.

:: 2. Use PowerShell to modify User PATH environment variable
echo [2/3] Registering current directory to User PATH...
powershell -NoProfile -Command ^
    "$currentPath = [Environment]::GetEnvironmentVariable('Path', 'User');" ^
    "$dir = '%CD%';" ^
    "if ($currentPath -split ';' -notcontains $dir) {" ^
    "    [Environment]::SetEnvironmentVariable('Path', $currentPath + ';' + $dir, 'User');" ^
    "    Write-Host 'Success: Added to Path environment variable.';" ^
    "} else {" ^
    "    Write-Host 'Info: Already present in PATH.';" ^
    "}"

echo.
echo [3/3] Setup Completed!
echo ===========================================
echo Please restart your terminal/cmd or run:
echo    refreshenv
echo Then verify by running: dbot --help
echo ===========================================
