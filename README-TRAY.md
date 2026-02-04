# Mail Agent - System Tray Application

Automated email management system that runs in your system tray.

## Quick Start

### For End Users (Using Compiled .exe)

1. Download the `MailAgent.zip` file
2. Extract to any folder (e.g., `C:\MailAgent`)
3. Double-click `MailAgent.exe`
4. Look for the envelope icon in your system tray

### For Developers (Build from Source)

#### 1. Install Dependencies
```bash
cd D:\mail-agent
.\venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-tray.txt
pip install pyinstaller
```

#### 2. Build Executable
```bash
pyinstaller mail_agent.spec
```

The executable will be created at: `dist\MailAgent.exe`

## Features

- ✅ Runs in system tray (no console window)
- ✅ Automatic email processing every 6 hours
- ✅ Spam/delete filtering
- ✅ AI summarization (GLM-4.5-Air)
- ✅ Telegram notifications
- ✅ GUI configuration editor
- ✅ Pause/resume functionality

## System Tray Menu

Right-click the tray icon to access:

- **About** - Author information
- **Configure** - Edit filter patterns
- **Pause/Resume** - Pause email checking
- **Exit** - Close application

## Configuration

### Using GUI (Recommended)

1. Right-click tray icon → **Configure**
2. Edit patterns in tabs:
   - **Trusted Senders** - Never filter these
   - **Spam Emails** - Exact emails → Spam
   - **Spam Domains** - Domains → Spam
   - **Spam Keywords** - Keywords → Spam
   - **Delete Emails** - Exact emails → Trash
   - **Delete Domains** - Domains → Trash
   - **Delete Keywords** - Keywords → Trash
3. Click **Save All**

### Manual Configuration

Edit files in `config/patterns/`:
- One entry per line
- Case-insensitive
- No special formatting needed

Example `delete_keywords.txt`:
```
unsubscribe
opt-out
remove from list
```

## Author

**Dr. Bounthong Vongxaya**  
Mobile/WhatsApp: 020 91316541

## License

MIT
