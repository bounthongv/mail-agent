# 🌐 Mail Agent - Ubuntu Server Setup Guide (Mobile/Web Version)

This guide explains how to host the Mail Agent "Brain" and "Dashboard" on your Ubuntu Cloud Server (`202.137.147.5`). This allows you to access your summaries from any iPad/iPhone/Android device 24/7 without draining their battery.

---

## 🏗️ Architecture Overview
*   **The Brain (Worker)**: Runs on Ubuntu, fetches mail 24/7.
*   **The Memory (Database)**: SQLite file stored on Ubuntu.
*   **The AI Engine**: Uses your Windows Cloud Server (`209.126.1.13`).
*   **The Bridge (API)**: FastAPI wrapper (port 8000) for Flutter app access.
*   **The Face (Dashboard)**: Streamlit web interface (port 8501).

---

## 🚀 Step-by-Step Installation

### 1. Prepare the Server
Connect to your Ubuntu server via SSH and ensure Python is ready:
```bash
sudo apt update
sudo apt install python3-pip python3-venv -y
```

### 2. Transfer the Code
Upload the `mobile-version` folder to your home directory on Ubuntu. You can use SCP, SFTP, or Git.

### 3. Install Dependencies
Navigate to the folder and install the required Python libraries:
```bash
cd mobile-version
# setup ven first
pip install -r requirements.txt
# Ensure specifically needed web/db libraries are present
pip install streamlit sqlalchemy passlib python-dotenv requests imap_tools fastapi uvicorn
```

### 4. Configure Environment Variables
Create or edit the `.env` file in the `mobile-version` directory:
```bash
nano .env
```

Add your configuration with **multi-user JSON structure** (matching your existing credentials):
```env
# AI Server Endpoints
WINDOWS_AI_URL=http://209.126.1.13:11434/api/generate
UBUNTU_AI_URL=http://localhost:11434/api/generate

# API Keys (Fallbacks)
GEMINI_API_KEY=your_gemini_key
TELEGRAM_BOT_TOKEN=your_bot_token

# Multi-User Configuration (JSON Array)
USERS_CONFIG=[{
  "user_id": "7252862418",
  "telegram_chat_id": "7252862418",
  "emails": [
    {
      "email": "bounthongv@gmail.com",
      "password": "pckq vqbi dlnd bsmm",
      "imap_host": "imap.gmail.com",
      "imap_port": 993,
      "enabled": true
    }
  ],
  "patterns": {
    "trusted_senders": "support@company.com,admin@company.com",
    "spam_keywords": "casino,poker,lottery,free money",
    "delete_keywords": "unsubscribe,promotional,newsletter"
  }
}]
```

**🔍 Key Changes:**
- ✅ **Email accounts & passwords**: Now in JSON structure within `USERS_CONFIG`
- ✅ **Telegram chat_id**: Per-user in the JSON structure  
- ✅ **Patterns**: Stored as JSON patterns for each user
- ✅ **Multi-user ready**: Add more user objects to the JSON array
- ✅ **Consistent**: Matches the structure of your existing `credentials.yaml`

---

## 🔄 User & Database Workflow

The system uses a **person_id** that you manually create in the `.env` file. This ID connects all data (email accounts, summaries, reports) to a specific user in the database.

### **1. You Create person_id in .env**
Manually assign unique person_ids in the `USERS_CONFIG` section of `.env`:
```env
USERS_CONFIG=[{
  "person_id": "john_doe_001",
  "telegram_chat_id": "7252862418",
  "emails": [
    {
      "email": "john@gmail.com",
      "password": "your_app_password",
      "imap_host": "imap.gmail.com",
      "imap_port": 993,
      "enabled": true
    }
  ],
  "patterns": {
    "trusted_senders": "support@company.com",
    "spam_keywords": "casino,lottery",
    "delete_keywords": "unsubscribe"
  }
}]
```

### **2. Database Stores person_id**
When the worker starts, it syncs data from `.env` to the database:
- **`EmailAccount.person_id`** - Groups all email accounts belonging to a person
- **`Summary.person_id`** - Allows queries like "all summaries for person X"

### **3. How It Works**
1. Worker reads `USERS_CONFIG` from `.env` on startup
2. Creates/updates email accounts in the database with your `person_id`
3. Every summary saved includes `person_id` for grouping
4. You can query: "All summaries for person_id 'john_doe_001'"

### **4. Benefits**
- ✅ You control person_id manually (no auto-generation)
- ✅ Consistent across `.env` and database
- ✅ Group multiple emails under one person
- ✅ Easy person-based queries and reports

**Example person_ids:** `user_001`, `john_doe`, `company_admin` - choose any unique identifier you prefer.

---

## 📱 Accessing from iPad / iPhone
1. Open **Safari** on your iPad.
2. Enter the URL: `http://202.137.147.5:8501`
3. **Pro Tip**: Tap the "Share" icon and select **"Add to Home Screen"**. The Mail Agent will now appear as a native App icon on your iPad!

---

## 🔒 Security Recommendations
1. **Firewall**: Ensure ports `8501` and `8000` are allowed in your Ubuntu firewall:
   ```bash
   sudo ufw allow 8501/tcp
   sudo ufw allow 8000/tcp
   ```
2. **Login**: Use the default credentials created during `init_db.py` (usually `admin` / `admin123`).
