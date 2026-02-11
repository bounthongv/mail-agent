# Mail Agent - Mobile/Web Version

This version of the Mail Agent is designed for iPad, iPhone, and Android users. It runs on a server and provides a beautiful web-based dashboard for viewing summaries and managing email accounts.

## 🚀 Quick Start (on your Notebook)

### 1. Install Dependencies
Make sure you have the new requirements installed:
```powershell
pip install -r mobile-version/requirements.txt
```

### 2. Configure AI Keys
Open `mobile-version/.env` and ensure your API keys are correct:
```env
GEMINI_API_KEY=your_key
HUGGINGFACE_API_KEY=your_key
NVIDIA_API_KEY=your_key
```

### 3. Start the Brain (Worker)
The worker checks for new emails every 10 minutes and saves summaries to the database.
```powershell
python mobile-version/worker.py
```

### 4. Start the Face (Dashboard)
Run the web interface:
```powershell
streamlit run mobile-version/dashboard.py
```

---

## 📱 How to access on iPad/iPhone
1. Ensure your computer and iPad are on the same Wi-Fi.
2. Find your computer's IP address (Run `ipconfig` in terminal).
3. On your iPad browser, go to: `http://YOUR_IP:8501`.
4. **Pro Tip**: Tap the "Share" button in Safari and select **"Add to Home Screen"** to make it look like a real App.

---

## 🛠 Features for Executives
- **Accounts Tab**: Add or remove email accounts directly from the iPad.
- **Dashboard Tab**: A clean, scrollable list of AI summaries.
- **Auto-Sync**: Summaries are saved in `data/mail_agent.db` so they are never lost.

---

## 🌍 How to deploy for your Friend
If you want your friend to use this from his house, you have two options:

### Option A: Local Tunnel (Easiest for testing)
1. Install [ngrok](https://ngrok.com/).
2. Run: `ngrok http 8501`.
3. Send the public `https://...` link to your friend.

### Option B: Hugging Face Spaces (Free Cloud Hosting)
1. Create a "New Space" on Hugging Face.
2. Select "Streamlit" as the SDK.
3. Upload the contents of the `mobile-version` folder.
4. It will run 24/7 for free!
