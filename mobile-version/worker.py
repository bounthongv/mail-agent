import sys
import os
import time
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

# Add the app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal, init_db
from db.models import EmailAccount, Summary, User
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

# Load user configurations from JSON
USERS_CONFIG = os.getenv("USERS_CONFIG", "[]")
try:
    USERS = json.loads(USERS_CONFIG)
except json.JSONDecodeError:
    print("❌ Invalid USERS_CONFIG in .env file")
    USERS = []

# Load Private AI IPs from environment
WINDOWS_AI_URL = os.getenv("WINDOWS_AI_URL", "http://209.126.1.13:11434/api/generate")
UBUNTU_AI_URL = os.getenv("UBUNTU_AI_URL", "http://202.137.147.5:11434/api/generate")

def initialize_user_accounts():
    """Initialize user accounts from USERS_CONFIG into database.
    
    Uses person_id from .env to group email accounts and summaries.
    Also creates User records for authentication.
    """
    db = SessionLocal()
    try:
        for user in USERS:
            person_id = user.get("person_id") or user.get("user_id")  # Support both keys
            telegram_chat_id = user.get("telegram_chat_id")
            patterns = user.get("patterns", {})
            temp_password = user.get("temp_password", "changeme123")  # Default temp password
            
            if not person_id:
                print("⚠️  Skipping user without person_id/user_id")
                continue
            
            # Create or update User record
            db_user = db.query(User).filter(User.person_id == person_id).first()
            if not db_user:
                db_user = User(person_id=person_id)
                db_user.set_password(temp_password)
                db.add(db_user)
                db.commit()
                print(f"✅ Created user: {person_id} (temp password set)")
            else:
                print(f"🔄 User exists: {person_id}")
            
            # Create or update EmailAccount records
            for email_config in user.get("emails", []):
                existing = db.query(EmailAccount).filter(
                    EmailAccount.email == email_config["email"]
                ).first()
                
                if not existing:
                    account = EmailAccount(
                        person_id=person_id,
                        user_id=db_user.id,
                        email=email_config["email"],
                        password=email_config["password"],
                        imap_host=email_config.get("imap_host", "imap.gmail.com"),
                        imap_port=email_config.get("imap_port", 993),
                        telegram_chat_id=telegram_chat_id,
                        trusted_senders=patterns.get("trusted_senders", ""),
                        spam_keywords=patterns.get("spam_keywords", ""),
                        delete_keywords=patterns.get("delete_keywords", ""),
                        enabled=email_config.get("enabled", True)
                    )
                    db.add(account)
                    print(f"✅ Added email account: {email_config['email']} (person: {person_id})")
                else:
                    # Update existing account
                    existing.person_id = person_id
                    existing.user_id = db_user.id
                    existing.telegram_chat_id = telegram_chat_id
                    existing.trusted_senders = patterns.get("trusted_senders", "")
                    existing.spam_keywords = patterns.get("spam_keywords", "")
                    existing.delete_keywords = patterns.get("delete_keywords", "")
                    existing.enabled = email_config.get("enabled", True)
                    print(f"🔄 Updated email account: {email_config['email']} (person: {person_id})")
            
            db.commit()
        
        account_count = db.query(EmailAccount).count()
        print(f"✅ Initialized {len(USERS)} users with {account_count} total email accounts")
    except Exception as e:
        print(f"❌ Error initializing users: {e}")
        db.rollback()
    finally:
        db.close()

def run_worker():
    print("🚀 Mail Agent Worker STARTED")
    
    # Initialize user accounts from USERS_CONFIG
    initialize_user_accounts()
    
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
                            person_id=acc.person_id,  # Store person_id for grouping
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
