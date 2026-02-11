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
from core.gemini_summarizer import GeminiSummarizer
from core.huggingface_summarizer import HuggingFaceSummarizer
from core.nvidia_summarizer import NvidiaSummarizer

# Load keys from environment
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
HF_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY", "")

def run_worker():
    print("🚀 Mail Agent Worker STARTED")
    db = SessionLocal()
    
    # Initialize summarizers
    gemini = GeminiSummarizer(api_key=GEMINI_KEY)
    hf = HuggingFaceSummarizer(api_key=HF_KEY)
    nvidia = NvidiaSummarizer(api_key=NVIDIA_KEY, model="moonshotai/kimi-k2.5")

    while True:
        accounts = db.query(EmailAccount).filter(EmailAccount.enabled == True).all()
        print(f"Checking {len(accounts)} accounts...")

        for acc in accounts:
            print(f"  - Processing: {acc.email}")
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

                    # Triple Fallback Chain
                    summary_text = gemini.summarize(email_data)
                    if "[Error" in summary_text:
                        print("      [Fallback 1] Trying HuggingFace...")
                        summary_text = hf.summarize(email_data)
                    
                    if "[Error" in summary_text:
                        print("      [Fallback 2] Trying NVIDIA...")
                        summary_text = nvidia.summarize(email_data)

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
                    
                    # Mark as read
                    fetcher.mark_as_read(email.uid)
                
                fetcher.disconnect()
            except Exception as e:
                print(f"    ❌ Error: {e}")

        print("Done. Sleeping for 10 minutes...")
        time.sleep(600)

if __name__ == "__main__":
    init_db()
    run_worker()
