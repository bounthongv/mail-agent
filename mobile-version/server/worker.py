"""
Mail Agent Server Worker
========================
Processes emails for all users based on their synced configs.
"""

import os
import sys
import time
import json
import yaml
from datetime import datetime, timedelta, timezone
from typing import Dict, List

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal, init_db
from db.models import Summary, UserConfig
from core.fetcher import EmailFetcher
from core.gemini_summarizer import GeminiSummarizer
from core.huggingface_summarizer import HuggingFaceSummarizer
from core.nvidia_summarizer import NvidiaSummarizer
from core.local_summarizer import LocalSummarizer
from reports.telegram_sender import TelegramSender

# === Load Server Config ===

def load_server_config():
    """Load server configuration from YAML"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'server.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

SERVER_CONFIG = load_server_config()

# AI Provider setup based on server config
def get_summarizer():
    """Get AI summarizer based on server config"""
    provider = SERVER_CONFIG['ai']['provider']
    api_keys = SERVER_CONFIG['api_keys']
    
    if provider == "gemini":
        return GeminiSummarizer(
            api_key=api_keys['gemini'],
            model=SERVER_CONFIG['ai'].get('model', 'gemini-2.0-flash'),
            max_tokens=SERVER_CONFIG['ai'].get('max_tokens', 300),
            temperature=SERVER_CONFIG['ai'].get('temperature', 0.3)
        )
    elif provider == "nvidia":
        return NvidiaSummarizer(
            api_key=api_keys['nvidia'],
            model=SERVER_CONFIG['ai'].get('model', 'moonshotai/kimi-k2.5')
        )
    elif provider == "huggingface":
        return HuggingFaceSummarizer(
            api_key=api_keys['huggingface'],
            model=SERVER_CONFIG['ai'].get('model', 'zai-org/GLM-4.7-Flash:novita')
        )
    elif provider == "ollama":
        local_ai = SERVER_CONFIG.get('local_ai', {})
        return LocalSummarizer(
            provider="ollama",
            model=SERVER_CONFIG['ai'].get('model', 'qwen2.5:3b'),
            url=local_ai.get('ubuntu_url', 'http://localhost:11434/api/generate')
        )
    else:
        # Default to Gemini
        return GeminiSummarizer(api_key=api_keys.get('gemini', ''))

# Telegram bot (shared for all users)
def get_telegram_sender():
    """Get Telegram sender with shared bot token"""
    bot_token = SERVER_CONFIG['telegram']['bot_token']
    return TelegramSender(bot_token=bot_token, chat_id=0)  # chat_id set per user

# === Worker Functions ===

def get_all_user_configs(db) -> List[Dict]:
    """Get all active user configs from database"""
    configs = db.query(UserConfig).filter(UserConfig.is_active == True).all()
    return [
        {
            'user_id': c.user_id,
            'config': json.loads(c.config_json),
            'last_sync': c.last_sync
        }
        for c in configs
    ]

def cleanup_old_summaries(db, retention_days: int = 30):
    """Delete summaries older than retention period"""
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    deleted = db.query(Summary).filter(Summary.created_at < cutoff).delete()
    db.commit()
    if deleted > 0:
        print(f"🗑️  Cleaned up {deleted} old summaries (older than {retention_days} days)")

def process_user_emails(user_data: Dict, summarizer, telegram_sender, db):
    """Process emails for a single user"""
    user_id = user_data['user_id']
    config = user_data['config']
    
    telegram_chat_id = config.get('telegram_chat_id')
    emails = config.get('emails', [])
    patterns = config.get('patterns', {})
    
    # Convert pattern lists to sets for fast lookup
    trusted_senders = set(patterns.get('trusted_senders', []))
    spam_keywords = set(patterns.get('spam_keywords', []))
    delete_keywords = set(patterns.get('delete_keywords', []))
    
    summaries_created = 0
    
    for email_config in emails:
        if not email_config.get('enabled', True):
            continue
            
        email_addr = email_config['email']
        password = email_config['password']
        imap_host = email_config.get('imap_host', 'imap.gmail.com')
        imap_port = email_config.get('imap_port', 993)
        
        print(f"  📧 Processing: {email_addr}")
        
        fetcher = EmailFetcher(
            email=email_addr,
            password=password,
            imap_host=imap_host,
            imap_port=imap_port
        )
        
        try:
            unread = fetcher.fetch_unread(limit=20)
            
            for email in unread:
                # Apply filters
                sender_lower = email.from_.lower()
                subject_lower = email.subject.lower()
                body_lower = (email.text or '').lower()
                
                # Check trusted
                if any(t.lower() in sender_lower for t in trusted_senders):
                    print(f"    ✓ [TRUSTED] {email.subject[:40]}")
                    fetcher.mark_as_read(email.uid)
                    continue
                
                # Check spam
                if any(kw.lower() in subject_lower or kw.lower() in body_lower for kw in spam_keywords):
                    print(f"    🚫 [SPAM] {email.subject[:40]}")
                    fetcher.move_to_spam(email.uid)
                    continue
                
                # Check delete
                if any(kw.lower() in subject_lower or kw.lower() in body_lower for kw in delete_keywords):
                    print(f"    🗑️ [DELETE] {email.subject[:40]}")
                    fetcher.delete_email(email.uid)
                    continue
                
                # Summarize
                print(f"    📝 Summarizing: {email.subject[:40]}")
                
                email_data = {
                    'from': email.from_,
                    'subject': email.subject,
                    'body': email.text or email.html
                }
                
                summary_text = summarizer.summarize(email_data)
                
                # Save to database
                new_summary = Summary(
                    user_id=user_id,
                    sender=email.from_,
                    subject=email.subject,
                    summary_text=summary_text,
                    received_at=email.date_obj or datetime.utcnow(),
                    synced=False
                )
                db.add(new_summary)
                db.commit()
                summaries_created += 1
                
                # Send to Telegram
                if telegram_chat_id:
                    telegram_sender.chat_id = int(telegram_chat_id)
                    telegram_sender.send_summary({
                        'summarized': [{
                            'subject': email.subject,
                            'summary': summary_text,
                            'from': email.from_
                        }],
                        'summarized_count': 1
                    })
                
                # Mark as read
                fetcher.mark_as_read(email.uid)
                
                # Small delay
                time.sleep(1)
            
            fetcher.disconnect()
            
        except Exception as e:
            print(f"    ❌ Error with {email_addr}: {str(e)[:50]}")
    
    return summaries_created

def run_worker():
    """Main worker loop"""
    print("="*50)
    print("🚀 Mail Agent Worker Started (v2.0)")
    print("="*50)
    print(f"📡 AI Provider: {SERVER_CONFIG['ai']['provider']}")
    print(f"⏱️  Interval: {SERVER_CONFIG['worker']['interval_minutes']} minutes")
    print("="*50)
    
    # Initialize database
    init_db()
    
    # Get summarizer and telegram
    summarizer = get_summarizer()
    telegram_sender = get_telegram_sender()
    
    interval = SERVER_CONFIG['worker']['interval_minutes'] * 60
    retention_days = SERVER_CONFIG['retention']['days']
    
    while True:
        try:
            db = SessionLocal()
            
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting check...")
            
            # Get all user configs
            user_configs = get_all_user_configs(db)
            print(f"👥 Found {len(user_configs)} active users")
            
            if not user_configs:
                print("   No users configured yet. Waiting for mobile sync...")
            else:
                total_summaries = 0
                
                for user_data in user_configs:
                    user_id = user_data['user_id']
                    print(f"\n👤 Processing user: {user_id}")
                    
                    summaries = process_user_emails(
                        user_data, summarizer, telegram_sender, db
                    )
                    total_summaries += summaries
                
                print(f"\n✅ Done! Created {total_summaries} summaries")
            
            # Cleanup old summaries
            if SERVER_CONFIG['retention']['auto_cleanup']:
                cleanup_old_summaries(db, retention_days)
            
            db.close()
            
            print(f"😴 Sleeping for {SERVER_CONFIG['worker']['interval_minutes']} minutes...")
            time.sleep(interval)
            
        except Exception as e:
            print(f"❌ Worker error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)  # Wait 1 minute before retry

if __name__ == "__main__":
    run_worker()
