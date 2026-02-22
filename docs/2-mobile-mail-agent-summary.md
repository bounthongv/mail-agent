# Mobile Mail Agent - Documentation

## Overview
The Mobile Mail Agent is a **server-based multi-user email automation system** with a unique architecture: **user configs are stored on mobile devices**, while the server handles email processing with admin-controlled AI settings.

## Architecture Philosophy

Unlike traditional systems where all data lives on a server, this version:
- **User Configs** → Stored on user's mobile device (YAML file)
- **AI Settings** → Admin-controlled on server only
- **Summaries** → Stored on server temporarily (30 days)

This gives users **control over their own credentials** while keeping sensitive AI keys secure on the server.

## Technical Stack

### Server Components
- **Language**: Python 3.8+
- **API Framework**: FastAPI (sync endpoint)
- **Database**: SQLite (summaries + cached configs)
- **Email Handling**: imap-tools
- **AI Integration**: Multiple providers (Gemini, OpenRouter, NVIDIA, etc.)
- **Messaging**: python-telegram-bot (shared bot for all users)

### Mobile App
- **Framework**: Flutter (Dart)
- **Platforms**: iOS, Android, Web
- **Storage**: Local YAML file (user_config.yaml)
- **Features**: Login, Dashboard, Config Editor, Sync

## Architecture Components

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SERVER (Admin Managed)                      │
├─────────────────────────────────────────────────────────────────────┤
│  mobile-version/server/                                             │
│  ├── config/                                                        │
│  │   └── server.yaml          # AI keys, bot token, settings       │
│  ├── user_configs/            # Backed up configs from sync        │
│  ├── data/                                                          │
│  │   └── mail_agent.db         # Summaries (30 day retention)      │
│  ├── sync_api.py              # FastAPI sync endpoint              │
│  ├── worker.py               # Background email processor          │
│  └── app/                                                           │
│      ├── db/models.py         # Summary + UserConfig models        │
│      ├── core/                # Fetcher + AI summarizers           │
│      └── reports/             # Telegram sender                    │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTPS (sync config & summaries)
                              │
┌─────────────────────────────────────────────────────────────────────┐
│                      MOBILE DEVICE (User Owned)                     │
├─────────────────────────────────────────────────────────────────────┤
│  flutter_app/                                                       │
│  └── lib/                                                           │
│      ├── main.dart             # App entry + auth                  │
│      ├── models/              # UserConfig, Summary models          │
│      ├── services/                                                  │
│      │   ├── config_service.dart  # Read/write local YAML          │
│      │   └── sync_service.dart    # API sync calls                 │
│      └── screens/                                                   │
│          ├── login_screen.dart    # User ID + Server URL           │
│          ├── dashboard_screen.dart # View summaries                │
│          └── config_screen.dart   # Edit emails + patterns         │
│                                                                     │
│  Local Storage:                                                     │
│  └── user_config.yaml         # User's credentials & patterns      │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Differences from PC Version

| Aspect | PC Version | Mobile Version |
|--------|------------|----------------|
| **Config Storage** | Server files | Mobile device (YAML) |
| **AI Settings** | User controlled | Admin controlled |
| **Users** | Single user | Multi-user |
| **Authentication** | None | User ID based |
| **UI** | System tray + tkinter | Flutter app |
| **Data Persistence** | Limited | 30 days on server |
| **Multi-device** | ❌ No | ✅ Yes (same user_id) |
| **Telegram Bot** | User's own bot | Shared bot (per-user chat_id) |

## Data Separation

### Admin Controls (Server - `config/server.yaml`)
```yaml
ai:
  provider: "gemini"
  model: "gemini-2.0-flash"
  
api_keys:
  gemini: "YOUR_API_KEY"
  openrouter: "YOUR_API_KEY"
  
telegram:
  bot_token: "123456789:ABC..."  # Shared for all users
  
worker:
  interval_minutes: 10
  
retention:
  days: 30
```

### User Controls (Mobile - `user_config.yaml`)
```yaml
user_id: "alice"
telegram_chat_id: "123456789"
server_url: "https://your-server.com"

emails:
  - email: "alice@gmail.com"
    password: "xxxx xxxx xxxx xxxx"
    imap_host: "imap.gmail.com"
    imap_port: 993
    enabled: true

patterns:
  trusted_senders:
    - "boss@company.com"
    - "family@gmail.com"
  spam_keywords:
    - "buy now"
    - "limited offer"
  delete_keywords:
    - "unsubscribe"
```

## How to Set Up

### Part 1: Server Setup (Admin)

#### 1. Install Dependencies
```bash
cd mobile-version/server
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### 2. Configure Server Settings
Edit `config/server.yaml`:
```yaml
ai:
  provider: "gemini"
  model: "gemini-2.0-flash"
  max_tokens: 300
  temperature: 0.3

api_keys:
  gemini: "YOUR_GEMINI_API_KEY"
  openrouter: "YOUR_OPENROUTER_KEY"
  huggingface: "YOUR_HF_TOKEN"
  nvidia: "YOUR_NVIDIA_KEY"

telegram:
  bot_token: "123456789:ABCdefGHIjkl..."

worker:
  interval_minutes: 10
  max_emails_per_check: 50

retention:
  days: 30
  auto_cleanup: true
```

#### 3. Start Services

**Terminal 1 - API Server:**
```bash
cd mobile-version/server
source venv/bin/activate
python sync_api.py
# Runs on http://0.0.0.0:8000
```

**Terminal 2 - Worker:**
```bash
cd mobile-version/server
source venv/bin/activate
python worker.py
# Runs every 10 minutes
```

#### 4. Production Deployment (Optional)
Use systemd, supervisor, or Docker to run as services.

### Part 2: Mobile App Setup (User)

#### 1. Build the App
```bash
cd flutter_app
flutter pub get
flutter run  # Debug mode

# Build for distribution
flutter build apk       # Android
flutter build ios       # iOS
flutter build web       # Web
```

#### 2. First Launch
1. Enter your **User ID** (unique identifier)
2. Enter **Server URL** (provided by admin)
3. Tap "Continue"

#### 3. Configure Your Account
1. Go to Settings (gear icon)
2. Add your email account(s)
3. Set your Telegram Chat ID
4. Configure patterns (trusted, spam, delete)
5. Tap "Save & Sync"

#### 4. Get Telegram Chat ID
1. Open Telegram
2. Search for `@userinfobot`
3. Start the bot
4. It will reply with your Chat ID

#### 5. Gmail App Password
1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Go to https://myaccount.google.com/apppasswords
4. Create App Password (16 characters)
5. Use this in the app (not your regular password)

## Data Flow

### Sync Flow
```
┌──────────────────────────────────────────────────────────────┐
│ 1. User opens app / taps Sync button                         │
│    ↓                                                          │
│ 2. App reads local user_config.yaml                          │
│    ↓                                                          │
│ 3. POST /sync with:                                          │
│    - user_id                                                  │
│    - telegram_chat_id                                        │
│    - emails (with passwords)                                 │
│    - patterns                                                 │
│    ↓                                                          │
│ 4. Server:                                                    │
│    - Saves config to database                                │
│    - Saves config to disk (backup)                           │
│    - Returns new summaries since last sync                   │
│    ↓                                                          │
│ 5. App displays summaries in dashboard                       │
└──────────────────────────────────────────────────────────────┘
```

### Worker Processing Flow
```
┌──────────────────────────────────────────────────────────────┐
│ Worker runs every 10 minutes                                 │
│    ↓                                                          │
│ For each active user config:                                 │
│    ↓                                                          │
│ 1. Load user's emails + patterns                             │
│    ↓                                                          │
│ 2. Connect to each email account via IMAP                    │
│    ↓                                                          │
│ 3. Fetch unread emails                                       │
│    ↓                                                          │
│ 4. Apply filters (trusted → spam → delete)                   │
│    ↓                                                          │
│ 5. Summarize remaining emails using AI                       │
│    ↓                                                          │
│ 6. Save summaries to database                                │
│    ↓                                                          │
│ 7. Send to user's Telegram (using their chat_id)            │
│    ↓                                                          │
│ 8. Mark emails as read                                       │
│    ↓                                                          │
│ Cleanup summaries older than 30 days                         │
└──────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | Health check | Server status |
| `GET /health` | Health check | Alias |
| `POST /sync` | Sync | Send config, receive summaries |
| `GET /summaries/{user_id}` | Query | Get summaries for user |
| `DELETE /config/{user_id}` | Delete | Remove user config |

### POST /sync Example
**Request:**
```json
{
  "user_id": "alice",
  "telegram_chat_id": "123456789",
  "emails": [
    {
      "email": "alice@gmail.com",
      "password": "xxxx xxxx xxxx xxxx",
      "imap_host": "imap.gmail.com",
      "imap_port": 993,
      "enabled": true
    }
  ],
  "patterns": {
    "trusted_senders": ["boss@company.com"],
    "spam_keywords": ["buy now", "limited offer"],
    "delete_keywords": ["unsubscribe"]
  },
  "last_sync_time": "2024-01-15T10:00:00"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Config synced. Found 5 new summaries.",
  "summaries": [
    {
      "id": 123,
      "sender": "boss@company.com",
      "subject": "Meeting Tomorrow",
      "summary_text": "Please join the meeting at 2 PM...",
      "received_at": "2024-01-15T09:30:00",
      "created_at": "2024-01-15T09:35:00"
    }
  ],
  "summaries_count": 5
}
```

## Multi-Device Support

Users can have **multiple devices** with the same User ID:
- Each device syncs independently
- All devices see the same summaries
- Config changes on one device sync to server
- Other devices get updates on next sync

## Security Considerations

### What's Secure
- ✅ AI API keys stay on server (admin only)
- ✅ Telegram bot token stays on server
- ✅ Configs transmitted via HTTPS (recommended)
- ✅ Summaries auto-deleted after 30 days

### What's Not Encrypted
- ⚠️ User credentials stored in plain text on device
- ⚠️ User ID is the only "authentication" (no password)
- ⚠️ Anyone with user_id can sync that user's data

### Recommendations
1. Use HTTPS in production
2. Use strong user IDs (not guessable)
3. Keep mobile device secure (screen lock)
4. Consider adding device PIN in app (future enhancement)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection failed" | Check server URL, ensure API is running |
| "No summaries" | Check worker is running, check email credentials |
| "Telegram not sending" | Verify chat_id is correct (from @userinfobot) |
| "AI not responding" | Check AI keys in server.yaml |
| "Config not saving" | Check app has storage permissions |
| "Gmail auth failed" | Use App Password, not regular password |
| Multiple devices not syncing | Ensure same user_id on all devices |

## File Locations

### Server
```
mobile-version/server/
├── config/server.yaml       # Admin settings
├── user_configs/*.yaml      # User config backups
├── data/mail_agent.db       # Summaries database
└── logs/                    # Worker logs
```

### Mobile Device
```
# Android:
/data/data/com.example.mail_agent/app_flutter/user_config.yaml

# iOS:
Library/Application Support/user_config.yaml

# Web:
localStorage (browser)
```

## Migration from PC Version

If moving from PC version:

1. **Export patterns** from `config/patterns/*.txt` files
2. **Convert to YAML format** for mobile app
3. **Set up server** with admin config
4. **Configure mobile app** with your emails and patterns
5. **Keep PC version** if you prefer local processing

## Comparison: Old Mobile vs New Mobile

| Feature | Old (Streamlit + SQLite) | New (Flutter + Local Config) |
|---------|--------------------------|------------------------------|
| Config Location | Server database | Mobile device |
| AI Keys | Per-user in .env | Admin-only on server |
| UI | Web browser | Native app |
| Offline | No | Partial (view cached) |
| Multi-device | No | Yes |
| User Control | Limited | Full control of own data |

## Next Steps

1. **Admin**: Set up server, configure AI, start services
2. **Users**: Install app, configure emails, sync
3. **Monitor**: Check worker logs for processing status
4. **Scale**: Add more users as needed

For questions or issues, check server logs and ensure both API and Worker are running.
