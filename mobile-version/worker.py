import sys
import os
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal, init_db
from db.models import EmailAccount, Summary
from core.fetcher import EmailFetcher
from core.local_summarizer import LocalSummarizer
from core.gemini_summarizer import GeminiSummarizer
from core.huggingface_summarizer import HuggingFaceSummarizer
from core.nvidia_summarizer import NvidiaSummarizer
from reports.telegram_sender import TelegramSender

# Load keys from environment
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
HF_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Load Private AI IPs from environment
WINDOWS_AI_URL = os.getenv("WINDOWS_AI_URL", "http://209.126.1.13:11434/api/generate")
UBUNTU_AI_URL = os.getenv("UBUNTU_AI_URL", "http://202.137.147.5:11434/api/generate")

def run_worker():
    print("🚀 Mail Agent Worker STARTED")
    db = SessionLocal()
    
    # Initialize summarizers
    windows_ai = LocalSummarizer(provider="ollama", model="kimi-k2.5:cloud", url=WINDOWS_AI_URL)
    ubuntu_ai = LocalSummarizer(provider="ollama", model="glm-4.6:cloud", url=UBUNTU_AI_URL)
    
    # Cloud fallbacks
    gemini = GeminiSummarizer(api_key=GEMINI_KEY)
    nvidia = NvidiaSummarizer(api_key=NVIDIA_KEY, model="moonshotai/kimi-k2.5")

    while True:
        try:
            accounts = db.query(EmailAccount).filter(EmailAccount.enabled == True).all()
            print(f"Checking {len(accounts)} accounts...")

            for acc in accounts:
                print(f"  - Processing: {acc.email}")
                
                # Setup per-user reporter
                user_bot = None
                if acc.telegram_chat_id and BOT_TOKEN:
                    user_bot = TelegramSender(bot_token=BOT_TOKEN, chat_id=acc.telegram_chat_id)

                fetcher = EmailFetcher(
                    email=acc.email,
                    password=acc.password,
                    imap_host=acc.imap_host,
                    imap_port=acc.imap_port
                )

                try:
                    unread = fetcher.fetch_unread(limit=10)
                    for email in unread:
                        print(f"    Summarizing: {email.subject[:30]}...")
                        
                        email_data = {
                            'from': email.from_,
                            'subject': email.subject,
                            'body': email.text or email.html
                        }

                        # --- NEW TIERED FALLBACK ---
                        # Tier 1: Windows Cloud AI
                        summary_text = windows_ai.summarize(email_data)
                        
                        # Tier 2: Ubuntu Cloud AI
                        if "[Error" in summary_text or "[Ollama error" in summary_text:
                            print("      [Fallback 1] Trying Ubuntu AI...")
                            summary_text = ubuntu_ai.summarize(email_data)
                        
                        # Tier 3: Gemini
                        if "[Error" in summary_text and GEMINI_KEY:
                            print("      [Fallback 2] Trying Gemini...")
                            summary_text = gemini.summarize(email_data)

                        # Save to DB
                        new_summary = Summary(
                            account_id=acc.id,
                            sender=email.from_,
                            subject=email.subject,
                            summary_text=summary_text,
                            received_at=email.date_obj or datetime.now()
                        )
                        db.add(new_summary)
                        db.commit()
                        
                        # Send to user's specific Telegram
                        if user_bot:
                            user_bot.send_summary({
                                'summarized': [{'subject': email.subject, 'summary': summary_text, 'from': email.from_}],
                                'summarized_count': 1,
                                'all_processed': 1
                            })
                        
                        # Mark as read
                        fetcher.mark_as_read(email.uid)
                    
                    fetcher.disconnect()
                except Exception as e:
                    print(f"    ❌ Error with account {acc.email}: {e}")

            print(f"Done. Sleeping for 10 minutes (at {datetime.now().strftime('%H:%M:%S')})...")
            time.sleep(600)
        except Exception as e:
            print(f"FATAL Worker Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    init_db()
    run_worker()

if __name__ == "__main__":
    init_db()
    run_worker()
