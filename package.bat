@echo off
echo ============================================
echo Mail Agent - Package for Distribution
echo ============================================
echo.

REM Create distribution folder
if exist "MailAgent-Package" rmdir /S /Q "MailAgent-Package"
mkdir "MailAgent-Package"

REM Copy executable
echo Copying executable...
copy "dist\MailAgent.exe" "MailAgent-Package\" >nul

REM Copy config folder
echo Copying configuration...
xcopy /E /I /Y "config" "MailAgent-Package\config" >nul

REM Copy README
echo Copying documentation...
copy "README-TRAY.md" "MailAgent-Package\README.md" >nul

echo.
echo ============================================
echo Package created: MailAgent-Package
echo ============================================
echo.
echo To distribute:
echo 1. Zip the "MailAgent-Package" folder
echo 2. Share the zip file
echo.
echo To run locally:
echo 1. Double-click MailAgent-Package\MailAgent.exe
echo 2. Look for the envelope icon in system tray
echo.
pause
