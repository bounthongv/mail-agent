# Mail Agent - Mobile Version (v2.0)

## 📱 Overview

The Mobile Mail Agent is a **server-based multi-user email automation system** with a Flutter mobile app. Unlike the PC version, user configs are stored on mobile devices while the server handles email processing with admin-controlled AI settings.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVER (Admin Managed)                   │
├─────────────────────────────────────────────────────────────┤
│  • FastAPI sync endpoint                                    │
│  • Background worker (email processor)                      │
│  • SQLite database (summaries + cached configs)             │
│  • AI integration (Gemini, NVIDIA, HuggingFace, Ollama)     │
│  • Telegram bot (shared for all users)                      │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTPS
                              │
┌─────────────────────────────────────────────────────────────┐
│                  MOBILE DEVICE (User Owned)                 │
├─────────────────────────────────────────────────────────────┤
│  • Flutter app (iOS, Android, Web)                          │
│  • Local YAML config storage                                │
│  • User controls: emails, patterns, Telegram chat ID        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Part 1: Server Setup (Admin)

#### 1. Install Dependencies
```bash
cd mobile-version/server
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### 2. Initialize Database
```bash
python init_db.py
```

#### 3. Configure Server Settings
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
  huggingface: "YOUR_HUGGINGFACE_TOKEN"
  nvidia: "YOUR_NVIDIA_API_KEY"

telegram:
  bot_token: "YOUR_TELEGRAM_BOT_TOKEN"

worker:
  interval_minutes: 10
  max_emails_per_check: 50

retention:
  days: 30
  auto_cleanup: true
```

#### 4. Start Services

**Terminal 1 - API Server:**
```bash
python sync_api.py
# Runs on http://0.0.0.0:8000
```

**Terminal 2 - Worker:**
```bash
python worker.py
# Runs every 10 minutes
```

---

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
2. Enter **Server URL** (e.g., `http://your-server.com:8000`)
3. Tap "Continue"

#### 3. Configure Your Account
1. Tap the gear icon (Settings)
2. Add your email account(s):
   - Email address
   - App password (for Gmail: use App Password, not regular password)
   - IMAP host and port
3. Set your **Telegram Chat ID**:
   - Open Telegram
   - Search for `@userinfobot`
   - Start the bot
   - It will reply with your Chat ID
4. Configure patterns:
   - **Trusted Senders**: Emails to skip AI check
   - **Spam Keywords**: Move to spam
   - **Delete Keywords**: Move to trash
5. Tap "Save & Sync"

#### 4. Gmail App Password Setup
1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Go to https://myaccount.google.com/apppasswords
4. Create App Password (16 characters)
5. Use this in the app (not your regular password)

---

## 📱 Accessing from Mobile Devices

### Option 1: Local Network (Same Wi-Fi)
1. Find your server's IP address:
   - Windows: `ipconfig` → Look for IPv4 Address
   - Linux/Mac: `ifconfig` → Look for inet
2. On mobile browser: `http://YOUR_SERVER_IP:8000` (for API)
3. For Flutter app: Enter the same URL in login screen

### Option 2: Public Deployment (Ngrok)
```bash
# Install ngrok, then:
ngrok http 8000
```
Use the provided `https://...` URL in the Flutter app.

### Option 3: Production Deployment
For production, deploy with:
- **Docker**: Containerize the server
- **Systemd**: Run as background service
- **Reverse Proxy**: Use Nginx with HTTPS

---

## 🛠 Features

### Mobile App
- **Dashboard**: View AI-summarized emails
- **Pull-to-Refresh**: Sync with server
- **Multi-Account Support**: Add multiple email accounts
- **Pattern Management**: Configure trusted senders, spam, delete keywords
- **Telegram Integration**: Receive summaries on Telegram
- **Offline Viewing**: View cached summaries

### Server
- **Multi-User**: Support unlimited users
- **AI Providers**: Gemini, NVIDIA, HuggingFace, Ollama
- **Auto-Cleanup**: Delete summaries older than 30 days
- **Background Worker**: Process emails every 10 minutes
- **Config Backup**: Save user configs to disk

---

## 📊 Data Flow

### Sync Flow
1. User opens app / taps Sync
2. App reads local `user_config.yaml`
3. POST `/sync` with config
4. Server saves config to database + disk backup
5. Server returns new summaries since last sync
6. App displays summaries

### Worker Processing Flow
1. Worker runs every 10 minutes
2. For each active user config:
   - Load emails + patterns
   - Connect via IMAP
   - Fetch unread emails
   - Apply filters (trusted → spam → delete)
   - Summarize with AI
   - Save to database
   - Send to Telegram
   - Mark as read
3. Cleanup old summaries

---

## 🔒 Security Considerations

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

---

## 📁 File Locations

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

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection failed" | Check server URL, ensure API is running |
| "No summaries" | Check worker is running, check email credentials |
| "Telegram not sending" | Verify chat_id is correct (from @userinfobot) |
| "AI not responding" | Check AI keys in server.yaml |
| "Config not saving" | Check app has storage permissions |
| "Gmail auth failed" | Use App Password, not regular password |
| Multiple devices not syncing | Ensure same user_id on all devices |

---

## 🔄 Migration from PC Version

If moving from PC version:

1. **Export patterns** from `config/patterns/*.txt` files
2. **Convert to YAML format** for mobile app
3. **Set up server** with admin config
4. **Configure mobile app** with your emails and patterns
5. **Keep PC version** if you prefer local processing

---

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | Health check | Server status |
| `GET /health` | Health check | Alias |
| `POST /sync` | Sync | Send config, receive summaries |
| `GET /summaries/{user_id}` | Query | Get summaries for user |
| `DELETE /config/{user_id}` | Delete | Remove user config |

---

## 🎯 Next Steps

1. **Admin**: Set up server, configure AI, start services
2. **Users**: Install app, configure emails, sync
3. **Monitor**: Check worker logs for processing status
4. **Scale**: Add more users as needed

For questions or issues, check server logs and ensure both API and Worker are running.
