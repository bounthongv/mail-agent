# Build Mail Agent Executable

## Prerequisites

Install PyInstaller and tray dependencies:
```bash
cd D:\mail-agent
.\venv\Scripts\activate
pip install -r requirements-tray.txt
pip install pyinstaller
```

## Build Steps

1. **Build the executable:**
```bash
pyinstaller mail_agent.spec
```

2. **The executable will be created at:**
```
dist\MailAgent.exe
```

3. **Copy config folder (if not included):**
```bash
xcopy /E /I config dist\config
```

## Running

Double-click `dist\MailAgent.exe` - it will:
- Start in system tray (no console window)
- Run email checks every 6 hours
- Right-click tray icon for menu

## Menu Options

- **About** - Shows author info
- **Configure** - Edit pattern files (spam, delete, trusted)
- **Pause** - Temporarily pause email checking
- **Exit** - Close the application

## Features

- ✅ Runs in system tray
- ✅ No console window
- ✅ Right-click context menu
- ✅ GUI configuration editor
- ✅ Pause/resume functionality
- ✅ Auto-starts on launch

## Troubleshooting

If config files are not found:
1. Ensure `config` folder is in same directory as `MailAgent.exe`
2. Or re-run: `xcopy /E /I config dist\config`

## Distribution

To distribute to others:
1. Copy entire `dist` folder
2. Rename to `MailAgent`
3. Zip and share
