"""Create distribution package for Mail Agent."""
import os
import shutil
import zipfile
from datetime import datetime

def create_package():
    # Create package directory
    package_dir = f"D:mail-agentMailAgent-Package-{datetime.now().strftime('%Y%m%d')}"
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)

    # Copy executable
    shutil.copy("dist/MailAgent.exe", package_dir)
    
    # Copy config directory
    shutil.copytree("config", os.path.join(package_dir, "config"))
    
    # Copy documentation
    docs = ["README.md", "USER-GUIDE.md", "BUILD.md"]
    for doc in docs:
        if os.path.exists(doc):
            shutil.copy(doc, package_dir)
    
    # Create installation script
    install_script = f"""@echo off
echo Installing Mail Agent...
echo.
echo 1. Creating shortcut on Desktop...
powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\Mail Agent.lnk'); $Shortcut.TargetPath = '%cd%\\MailAgent.exe'; $Shortcut.Save()"

echo 2. Adding to Windows Startup (optional)...
echo Press Y to add to startup, N to skip:
set /p choice=
if /i "%choice%"=="Y" (
    powershell "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\Mail Agent.lnk'); $Shortcut.TargetPath = '%cd%\\MailAgent.exe'; $Shortcut.Save()"
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
"""
    
    with open(os.path.join(package_dir, "install.bat"), "w") as f:
        f.write(install_script)

    # Create README for package
    package_readme = f"""# Mail Agent - Installation Package

## Quick Install
1. Extract all files to a folder (e.g., C:\\MailAgent)
2. Run `install.bat` to create shortcuts
3. Launch MailAgent.exe from desktop shortcut

## Configuration (Built-in GUI)
1. Right-click the envelope icon 📧 in system tray
2. Select **"Configure"** 
3. Use the tabbed interface to:
   - **Email Accounts**: Add Gmail accounts (enable 2FA first)
   - **Telegram**: Add bot token & Chat ID
   - **AI Settings**: Choose provider and enter API key
   - **Pattern Files**: Edit spam/delete filters
4. Click **"Save All Settings"**

## Files Included
- `MailAgent.exe` - Complete standalone application
- `config/` - Configuration files (created automatically)
- `install.bat` - Desktop shortcut creator

## No Setup Required!
Everything is built into MailAgent.exe - just run and configure through the GUI

## Support
- Dr. Bounthong Vongxaya
- Mobile/WhatsApp: 020 91316541
- Generated: {datetime.now().strftime('%Y-%m-%d')}
"""

    with open(os.path.join(package_dir, "README-PACKAGE.md"), "w", encoding='utf-8') as f:
        f.write(package_readme)

    # Create ZIP
    zip_name = f"MailAgent-Package-{datetime.now().strftime('%Y%m%d')}.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zf.write(file_path, arcname)

    print(f"Package created: {zip_name}")
    print(f"Folder: {package_dir}")

if __name__ == "__main__":
    create_package()