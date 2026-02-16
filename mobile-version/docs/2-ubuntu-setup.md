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
pip install -r requirements.txt
# Ensure specifically needed web/db libraries are present
pip install streamlit sqlalchemy passlib python-dotenv requests imap_tools fastapi uvicorn
```

### 4. Configure Environment Variables
Create or edit the `.env` file in the `mobile-version` directory:
```bash
nano .env
```
Add your configuration (matching your Private AI setup):
```env
# AI Server Endpoints
WINDOWS_AI_URL=http://209.126.1.13:11434/api/generate
UBUNTU_AI_URL=http://localhost:11434/api/generate

# API Keys (Fallbacks)
GEMINI_API_KEY=your_gemini_key
TELEGRAM_BOT_TOKEN=your_bot_token
```

### 5. Initialize the Database
This creates the `data/mail_agent.db` file where all summaries and accounts are stored.
```bash
python3 init_db.py
```

### 6. Start the Background Worker (The Brain)
Use `nohup` to keep the worker running even after you disconnect from SSH:
```bash
nohup python3 worker.py > worker.log 2>&1 &
```
*To check if it's running:* `tail -f worker.log`

### 7. Start the Web Dashboard (The Face)
Run Streamlit and bind it to your public IP:
```bash
nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &
```

### 8. Start the Flutter API Wrapper (The Bridge)
Run the FastAPI service to allow your Flutter app to fetch summaries:
```bash
nohup python3 api.py > api.log 2>&1 &
```
*The API will run on port 8000.*

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
