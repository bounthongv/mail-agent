# PC Mail Agent - Documentation

## Overview
The PC Mail Agent is a **Windows desktop application** that runs locally on your computer to automatically fetch, filter, and summarize emails. It operates from the system tray with a context menu for easy management.

## Purpose
- **Automate email processing** on your personal computer
- **Filter spam and unwanted emails** automatically
- **Summarize important emails** using AI
- **Send daily reports** to Telegram
- **Run continuously** in the background via system tray

## Technical Stack

### Core Technologies
- **Language**: Python 3.8+
- **GUI Framework**: 
  - `pystray` - System tray icon and menu
  - `tkinter` - Pattern editor and debug log windows
  - `PIL/Pillow` - Icon generation
- **Build Tool**: PyInstaller (creates .exe from Python)
- **Email Handling**: `imap-tools` library
- **Configuration**: PyYAML (YAML files)
- **AI Integration**: Multiple providers (OpenRouter, Gemini, Ollama, etc.)
- **Messaging**: `python-telegram-bot`

### File Structure
```
mail-agent/
├── tray_app.py              # System tray application entry
├── src/
│   ├── main.py             # Core email processing logic
│   ├── config_loader.py    # Configuration loading
│   ├── scheduler.py        # Scheduling logic
│   ├── email_handler/
│   │   └── fetcher.py     # IMAP email fetching
│   ├── filters/            # Spam/delete filters
│   ├── summarizer/         # AI summarization classes
│   └── reports/
│       └── telegram_sender.py
├── config/
│   ├── settings.yaml       # App settings (interval, AI config)
│   ├── credentials.yaml    # Secrets (git-ignored)
│   └── patterns/           # Filter pattern files
├── requirements.txt        # Python dependencies
└── MailAgent.spec         # PyInstaller build config
```

## How to Set Up

### 1. Initial Setup
```bash
# Navigate to project
cd D:\mail-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration Files

#### A. Settings (`config/settings.yaml`)
```yaml
schedule:
  enabled: true
  interval_hours: 6                    # How often to check emails

ai:
  provider: "ollama"                   # AI provider: ollama/gemini/openrouter/etc
  model: "qwen2.5:3b"                  # AI model name
  max_tokens: 300
  temperature: 0.3

localai:
  enabled: true
  url: "http://localhost:11434/api/generate"  # Ollama URL

report:
  daily_summary: true                  # Send Telegram reports
  max_emails_per_report: 20
```

#### B. Credentials (`config/credentials.yaml`)
```yaml
emails:
  - email: your-email@gmail.com
    password: xxxx xxxx xxxx xxxx      # Gmail App Password (16 chars)
    imap_host: imap.gmail.com
    imap_port: 993
    enabled: true

telegram:
  bot_token: "123456789:ABC..."        # From @BotFather
  chat_id: 123456789                   # From @userinfobot

# AI Provider API Keys (add as needed)
openrouter:
  api_key: "sk-or-v1-..."
gemini:
  api_key: "AIza..."
```

#### C. Pattern Files (`config/patterns/`)
Create text files with one pattern per line:
- `trusted_senders.txt` - Skip filtering (exact emails)
- `spam_emails.txt` - Move to spam (exact match)
- `spam_domains.txt` - Move to spam (domain match)
- `spam_keywords.txt` - Move to spam (subject/body keywords)
- `delete_emails.txt` - Delete emails (exact match)
- `delete_domains.txt` - Delete emails (domain match)
- `delete_keywords.txt` - Delete emails (keywords)

### 3. Gmail App Password Setup (Required for Gmail)
1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Go to https://myaccount.google.com/apppasswords
4. Create App Password (16 characters, no spaces)
5. Use this in `credentials.yaml`

## How to Run

### Development/Testing Mode
```bash
# Activate venv and run
venv\Scripts\activate
python src\main.py
```

### Using System Tray App (Recommended)
```bash
venv\Scripts\activate
python tray_app.py
```
The tray icon appears in your system tray. Right-click for:
- **About** - App information
- **Edit Patterns** - GUI pattern editor
- **View Debug Log** - Real-time processing log
- **Start/Pause Processing** - Control email checking
- **Exit** - Close application

### Build Executable (For Distribution)
```bash
# Build single .exe file
pyinstaller MailAgent.spec

# Or use build script
python build_new.py

# Output: dist/MailAgent.exe
```

**After building:**
- Copy `config/` folder to `dist/config/`
- Run `dist/MailAgent.exe` directly (no Python needed)

## Workflow & Filter Priority

The system processes emails in two passes:

### Pass 1: Maintenance Scan (Newest 50 emails)
Applies filters in order:
1. **Trusted Senders** → Skip (keep as unread)
2. **Spam Emails** → Move to Spam folder
3. **Spam Domains** → Move to Spam folder
4. **Spam Keywords** → Move to Spam folder
5. **Delete Emails** → Move to Trash
6. **Delete Domains** → Move to Trash
7. **Delete Keywords** → Move to Trash

### Pass 2: Unread Scan (Up to 200 unread)
- Skip emails older than 30 days
- Apply filters again
- Summarize remaining emails
- Mark as read after summarization
- Send summaries to Telegram

### AI Fallback Chain
If primary AI fails, it automatically tries:
1. Primary Local AI (Ollama)
2. Secondary Local AI (Windows)
3. Configured Cloud Provider
4. NVIDIA → Gemini → HuggingFace → OpenRouter

## Telegram Reports

The bot sends formatted reports including:
- **Summary statistics** (scanned, spam, deleted, summarized)
- **Email summaries** grouped by account
- **Spam/Delete details** with reasons

## Testing Commands

```bash
# Test configuration
python test_system.py

# Run specific test
python -c "from test_system import test_config; test_config()"

# Check email fetch flags
python check_fetch_flags.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Bad credentials" | Use Gmail App Password, not regular password |
| AI not responding | Check Ollama is running: `ollama serve` |
| No Telegram messages | Verify bot_token and chat_id |
| Build fails | Ensure all imports in hiddenimports |

## Security Notes

- **Never commit `credentials.yaml`** - it's in .gitignore
- Use App Passwords for Gmail (not your real password)
- Pattern files may contain sensitive info
- The executable contains all credentials - keep it secure
