# Hugging Face Spaces Deployment Guide

This guide explains how to host your Mail Agent on **Hugging Face Spaces** so that your friend can access it on his iPad from anywhere in the world.

## 1. Create your Hugging Face Space
1. Log in to [Hugging Face](https://huggingface.co/).
2. Go to **New Space**: [huggingface.co/new-space](https://huggingface.co/new-space).
3. **Space Name**: Give it a name (e.g., `my-mail-agent`).
4. **SDK**: Select **Streamlit**.
5. **Space Hardware**: Choose **CPU Basic (Free)**.
6. **Visibility**: Select **Private** (recommended) so only you and your friend can see the emails.

## 2. Configure Your Secrets (API Keys)
On Hugging Face, we don't upload the `.env` file. Instead, we use "Secrets."
1. In your new Space, go to the **Settings** tab.
2. Scroll down to **Variables and secrets**.
3. Click **New secret** for each of these:
   - `GEMINI_API_KEY`: Your Google key.
   - `HUGGINGFACE_API_KEY`: Your HF token.
   - `NVIDIA_API_KEY`: Your NVIDIA key.
   - `TELEGRAM_BOT_TOKEN`: Your bot token.
   - `TELEGRAM_CHAT_ID`: Your chat ID.

## 3. Prepare the Files for Upload
Upload the following files from your `mobile-version/` folder to the Space:
- `app/` (all subfolders: core, db, api, dashboard)
- `config/` (patterns folder only)
- `dashboard.py`
- `worker.py`
- `requirements.txt`

## 4. How the Service Starts
Hugging Face Spaces look for a file named `app.py` or the main Streamlit file to run. 
To ensure **both** the Dashboard and the Worker run at the same time, we recommend adding a small "Start Worker" block to the top of your `dashboard.py`.

### Unified Start Logic (Add to dashboard.py):
```python
import threading
from worker import run_worker

# Start the background mail-checker thread if not already running
if 'worker_started' not in st.session_state:
    thread = threading.Thread(target=run_worker, daemon=True)
    thread.start()
    st.session_state['worker_started'] = True
```

## 5. Sharing with your Friend
1. Once the Space is "Running," copy the URL from your browser.
2. Send this link to your friend.
3. If the Space is **Private**, you can add your friend's Hugging Face username in the **Settings -> User management** section so he can log in.

## 6. Important Note on Data Persistence
In the Free tier of Hugging Face Spaces, the `mail_agent.db` file will be **erased** every time the Space restarts (usually once a day).
- **For Testing**: This is fine. Your friend just adds his email again.
- **For Permanent Use**: You can upgrade to a "Persistent Storage" tier in the Settings for a small monthly fee, or we can configure the app to sync the database to a private HF Dataset.
