@echo off
echo.
echo ==================================================
echo   Building Mail Agent Tray (MailAgent.exe)
echo ==================================================
echo.

REM Activate venv
call venv\Scripts\activate

REM Run PyInstaller
python -m PyInstaller ^
    --name=MailAgent ^
    --onefile ^
    --noconsole ^
    --add-data="config;config" ^
    --add-data="src;src" ^
    --hidden-import="pystray._win32" ^
    --hidden-import="PIL._tkinter_finder" ^
    --hidden-import="telegram" ^
    --hidden-import="imap_tools" ^
    --hidden-import="yaml" ^
    --hidden-import="requests" ^
    --icon="mail_agent.ico" ^
    --noconfirm ^
    tray_app.py

echo.
echo Done! New executable is in the 'dist' folder.
pause
