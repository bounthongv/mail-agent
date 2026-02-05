@echo off
echo Installing Mail Agent...
echo.
echo 1. Creating shortcut on Desktop...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Mail Agent.lnk'); $Shortcut.TargetPath = '%cd%\MailAgent.exe'; $Shortcut.Save()"

echo 2. Adding to Windows Startup (optional)...
echo Press Y to add to startup, N to skip:
set /p choice=
if /i "%choice%"=="Y" (
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Mail Agent.lnk'); $Shortcut.TargetPath = '%cd%\MailAgent.exe'; $Shortcut.Save()"
    echo Added to startup!
)

echo.
echo Installation complete!
echo.
echo NEXT STEPS:
echo 1. Run MailAgent.exe from desktop or start menu
echo 2. Right-click the envelope icon in system tray
echo 3. Select "Configure" to set up emails and API keys
echo 4. Add your Gmail accounts (enable 2FA and use App Passwords)
echo 5. Configure Telegram bot token and Chat ID
echo 6. Choose AI provider (OpenRouter recommended)
echo.
pause
