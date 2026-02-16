"""Mail Agent - Email Automation System.

Workflow:
1. Fetch ALL emails (read + unread) → Apply spam/delete filters
2. Fetch UNREAD emails only → Summarize and send to Telegram
"""

import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import load_config, AppConfig
from email_handler.fetcher import EmailFetcher, EmailMessage
from filters.domain_filter import DomainFilter
from filters.keyword_filter import KeywordFilter
from filters.delete_filter import DeleteFilter
from filters.delete_domain_filter import DeleteDomainFilter
from filters.delete_email_filter import DeleteEmailFilter
from filters.spam_email_filter import SpamEmailFilter
from summarizer.openrouter_summarizer import OpenRouterSummarizer
from summarizer.deepseek_summarizer import DeepSeekSummarizer
from summarizer.gemini_summarizer import GeminiSummarizer
from summarizer.huggingface_summarizer import HuggingFaceSummarizer
from summarizer.nvidia_summarizer import NvidiaSummarizer
from summarizer.groq_summarizer import GroqSummarizer
from summarizer.local_summarizer import LocalSummarizer
from reports.telegram_sender import TelegramSender
from scheduler import Scheduler


class MailAgent:
    def __init__(self, config: AppConfig):
        self.config = config
        # Check if running from executable (PyInstaller)
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.join(os.path.dirname(__file__), '..')
        self.base_path = os.path.join(base_dir, 'config', 'patterns')

        self.spam_email_filter = SpamEmailFilter(
            os.path.join(self.base_path, 'spam_emails.txt')
        )
        self.domain_filter = DomainFilter(
            os.path.join(self.base_path, 'spam_domains.txt')
        )
        self.keyword_filter = KeywordFilter(
            os.path.join(self.base_path, 'spam_keywords.txt')
        )
        self.delete_email_filter = DeleteEmailFilter(
            os.path.join(self.base_path, 'delete_emails.txt')
        )
        self.delete_domain_filter = DeleteDomainFilter(
            os.path.join(self.base_path, 'delete_domains.txt')
        )
        self.delete_filter = DeleteFilter(
            os.path.join(self.base_path, 'delete_keywords.txt')
        )

        # Cache trusted senders
        self.trusted_senders = self._load_trusted_senders()

        # Initialize dedicated fallback summarizers
        self.ollama_summarizer = LocalSummarizer(
            provider="ollama", 
            model=config.localai.model,
            url=config.localai.url
        )
        
        # Secondary Local Fallback (Windows)
        self.windows_summarizer = None
        if config.localai.secondary_url:
            self.windows_summarizer = LocalSummarizer(
                provider="ollama",
                model=config.localai.secondary_model or config.localai.model,
                url=config.localai.secondary_url
            )
            
        self.qwen_summarizer = LocalSummarizer(provider="qwen", model="qwen2.5:3b")

        # Priority: Configured provider -> Fallback chain
        provider = config.ai.provider.lower()
        
        if provider == "openrouter":
            print(f"Using OpenRouter API ({config.ai.model})")
            self.summarizer = OpenRouterSummarizer(
                api_key=config.openrouter.api_key,
                model=config.ai.model,
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
        elif provider == "gemini":
            print(f"Using Google Gemini API ({config.ai.model})")
            self.summarizer = GeminiSummarizer(
                api_key=config.gemini.api_key,
                model=config.ai.model if config.ai.model else "gemini-2.0-flash",
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
        elif provider == "ollama":
            print(f"Using Local Ollama ({config.localai.model})")
            self.summarizer = self.ollama_summarizer
        elif provider == "local" or provider == "qwen":
            print(f"Using Local Qwen CLI")
            self.summarizer = self.qwen_summarizer
        elif provider == "deepseek":
            print(f"Using DeepSeek API ({config.ai.model})")
            self.summarizer = DeepSeekSummarizer(
                api_key=config.deepseek.api_key,
                model=config.ai.model if config.ai.model else "deepseek-chat",
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
        elif provider == "huggingface":
            print(f"Using Hugging Face API ({config.ai.model})")
            self.summarizer = HuggingFaceSummarizer(
                api_key=config.huggingface.api_key,
                model=config.ai.model if config.ai.model else "zai-org/GLM-4.7-Flash:novita",
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
        elif provider == "nvidia":
            print(f"Using NVIDIA NIM API ({config.ai.model})")
            self.summarizer = NvidiaSummarizer(
                api_key=config.nvidia.api_key,
                model=config.ai.model if config.ai.model else "moonshotai/kimi-k1.5",
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
        elif provider == "groq":
            print(f"Using Groq API ({config.ai.model})")
            self.summarizer = GroqSummarizer(
                api_key=config.groq.api_key,
                model=config.ai.model if config.ai.model else "llama-3.1-8b-instant",
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
            # Fallback chain if provider is not explicitly set or recognized
            if config.gemini.api_key and config.gemini.api_key not in ["", "YOUR_GEMINI_API_KEY_HERE"]:
                print("Using Google Gemini API (fallback)")
                self.summarizer = GeminiSummarizer(
                    api_key=config.gemini.api_key,
                    model="gemini-2.0-flash",
                    max_tokens=config.ai.max_tokens,
                    temperature=config.ai.temperature
                )
            elif config.huggingface.api_key and config.huggingface.api_key not in ["", "YOUR_HF_TOKEN_HERE"]:
                print("Using Hugging Face API (fallback)")
                self.summarizer = HuggingFaceSummarizer(
                    api_key=config.huggingface.api_key,
                    model="zai-org/GLM-4.7-Flash:novita",
                    max_tokens=config.ai.max_tokens,
                    temperature=config.ai.temperature
                )
            elif config.openrouter.api_key and config.openrouter.api_key not in ["", "YOUR_OPENROUTER_API_KEY_HERE"]:
                print(f"Using OpenRouter API (fallback: {config.ai.model})")
                self.summarizer = OpenRouterSummarizer(
                    api_key=config.openrouter.api_key,
                    model=config.ai.model,
                    max_tokens=config.ai.max_tokens,
                    temperature=config.ai.temperature
                )
            else:
                print("Using Local Ollama (final fallback)")
                self.summarizer = self.ollama_summarizer

        self.telegram_sender = TelegramSender(
            bot_token=config.telegram.bot_token,
            chat_id=config.telegram.chat_id
        )

    def run_once(self, check_stop=None) -> Dict:
        """Run email processing in a single efficient pass.
        
        Args:
            check_stop: Optional callback that returns True if processing should stop.
        """
        report = {
            'all_processed': 0,
            'spam_count': 0,
            'deleted_count': 0,
            'summarized_count': 0,
            'summarized': [],
            'spam_details': [],
            'deleted_details': [],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'by_account': {}  # New: Track stats per account
        }

        for email_config in self.config.emails:
            # Check for stop signal between accounts
            if check_stop and check_stop():
                print("🛑 Processing stopped by user.")
                break

            if not email_config.enabled:
                print(f"Skipping disabled email: {email_config.email}")
                continue

            # Initialize account stats
            report['by_account'][email_config.email] = {
                'processed': 0,
                'spam': 0,
                'deleted': 0,
                'summarized': 0,
                'summaries': []
            }
            account_stats = report['by_account'][email_config.email]

            print(f"\n{'='*50}")
            print(f"Processing: {email_config.email}")
            print('='*50)

            fetcher = EmailFetcher(
                email=email_config.email,
                password=email_config.password,
                imap_host=email_config.imap_host,
                imap_port=email_config.imap_port,
                timeout=120
            )

            try:
                processed_uids = set()

                # PASS 1: Fetch newest 50 emails (Maintenance: Spam/Delete check)
                print("\n--- Pass 1: Maintenance Scan (Newest 50) ---")
                
                # Check stop signal before fetch
                if check_stop and check_stop():
                    print("🛑 Processing stopped by user.")
                    break
                    
                recent_emails = fetcher.fetch_all(limit=50)
                
                for email in recent_emails:
                    if check_stop and check_stop():
                        break

                    processed_uids.add(email.uid)
                    report['all_processed'] += 1
                    account_stats['processed'] += 1
                    
                    result = self._apply_filters(fetcher, email)
                    if result['action'] == 'spam':
                        print(f"  [{email.date}] [SPAM] {email.subject[:40]}")
                        report['spam_count'] += 1
                        account_stats['spam'] += 1
                        report['spam_details'].append({'from': email.from_, 'subject': email.subject, 'reason': result['reason']})
                    elif result['action'] == 'deleted':
                        print(f"  [{email.date}] [DELETED] {email.subject[:40]}")
                        report['deleted_count'] += 1
                        account_stats['deleted'] += 1
                        report['deleted_details'].append({'from': email.from_, 'subject': email.subject, 'reason': result['reason']})
                    elif result['action'] == 'trusted':
                        print(f"  [{email.date}] [TRUSTED] {email.from_[:40]}")
                
                if check_stop and check_stop():
                    print("🛑 Processing stopped by user.")
                    break

                # PASS 2: Fetch UNREAD emails (Summarization)
                print("\n--- Pass 2: Unread Scan (Up to 200) ---")
                # Using fetch_unread ensures we find unread emails even if they are old (deep in inbox)
                unread_emails = fetcher.fetch_unread(limit=200)
                
                # Define cutoff for "old" emails (e.g., 30 days)
                cutoff_days = 30
                now_utc = datetime.now(timezone.utc)
                
                for i, email in enumerate(unread_emails):
                    if check_stop and check_stop():
                        print("🛑 Processing stopped by user.")
                        break

                    # Check age of email
                    is_old = False
                    if email.date_obj:
                        # Ensure date_obj has timezone info to compare with now_utc
                        # imap_tools usually returns offset-aware datetime
                        try:
                            email_age = now_utc - email.date_obj if email.date_obj.tzinfo else datetime.now() - email.date_obj
                            if email_age.days > cutoff_days:
                                is_old = True
                        except Exception:
                            # If comparison fails, assume it's new to be safe, or just ignore
                            pass

                    # Skip if already processed in Pass 1 (unless we want to double check, but filters already ran)
                    if email.uid in processed_uids:
                         pass

                    # Apply filters again just in case (fast)
                    result = self._apply_filters(fetcher, email)
                    if result['action'] in ['spam', 'deleted']:
                        # Already handled or needs handling
                        if email.uid not in processed_uids:
                             if result['action'] == 'spam':
                                 print(f"  [{email.date}] [SPAM] {email.subject[:40]}")
                                 report['spam_count'] += 1
                                 account_stats['spam'] += 1
                                 report['spam_details'].append({'from': email.from_, 'subject': email.subject, 'reason': result['reason']})
                             else:
                                 print(f"  [{email.date}] [DELETED] {email.subject[:40]}")
                                 report['deleted_count'] += 1
                                 account_stats['deleted'] += 1
                                 report['deleted_details'].append({'from': email.from_, 'subject': email.subject, 'reason': result['reason']})
                        continue
                    
                    # Handle Old Emails (Skip summary, just mark read)
                    if is_old:
                        print(f"  [{email.date}] [OLD > {cutoff_days}d] Skipping summary, marking read: {email.subject[:40]}")
                        fetcher.mark_as_read(email.uid)
                        continue

                    # Summarize New Unread Emails
                    print(f"\n[{i+1}/{len(unread_emails)}] [{email.date}] Unread: {email.subject[:40]} {email.labels}")
                    summary = self._summarize_email(email)
                    if summary:
                        print(f"  [SUMMARY] {summary[:60]}...")
                        report['summarized_count'] += 1
                        account_stats['summarized'] += 1
                        
                        summary_entry = {
                            'account': email_config.email,
                            'from': email.from_,
                            'subject': email.subject,
                            'summary': summary
                        }
                        
                        report['summarized'].append(summary_entry)
                        account_stats['summaries'].append(summary_entry)
                        
                        fetcher.mark_as_read(email.uid)

                fetcher.disconnect()

            except Exception as e:
                print(f"Error processing {email_config.email}: {e}")
                import traceback
                traceback.print_exc()
                continue

        return report

    def _apply_filters(self, fetcher: EmailFetcher, email: EmailMessage) -> Dict:
        """Apply all filters to email. Return action taken."""
        result = {'action': 'unknown', 'reason': None}

        # 1. Check trusted senders (skip filtering, but mark as keep)
        if self._is_trusted(email.from_):
            print(f"  [TRUSTED] {email.from_[:40]}")
            result['action'] = 'trusted'
            return result

        # 2. Check spam emails (exact match)
        if self.spam_email_filter.is_spam(email.from_):
            emails = self.spam_email_filter.get_matching_emails(email.from_)
            print(f"  [SPAM email] {email.from_[:40]}")
            fetcher.move_to_spam(email.uid)
            result['action'] = 'spam'
            result['reason'] = f"Spam email: {', '.join(emails)}"
            return result

        # 3. Check spam domains
        if self.domain_filter.is_spam(email.from_):
            domains = self.domain_filter.get_matching_domains(email.from_)
            print(f"  [SPAM domain] {email.from_[:40]}")
            fetcher.move_to_spam(email.uid)
            result['action'] = 'spam'
            result['reason'] = f"Domain: {', '.join(domains)}"
            return result

        # 4. Check spam keywords (matches subject OR body)
        if self.keyword_filter.is_spam(email.subject, email.text):
            keywords = self.keyword_filter.get_matching_keywords(email.subject, email.text)
            print(f"  [SPAM keywords] {email.subject[:40]}")
            fetcher.move_to_spam(email.uid)
            result['action'] = 'spam'
            result['reason'] = f"Keywords: {', '.join(keywords)}"
            return result

        # 5. Check delete emails (exact match)
        if self.delete_email_filter.should_delete(email.from_):
            emails = self.delete_email_filter.get_matching_emails(email.from_)
            print(f"  [DELETE email] {email.from_[:40]}")
            fetcher.delete_email(email.uid)
            result['action'] = 'deleted'
            result['reason'] = f"Delete email: {', '.join(emails)}"
            return result

        # 6. Check delete domains
        if self.delete_domain_filter.should_delete(email.from_):
            domains = self.delete_domain_filter.get_matching_domains(email.from_)
            print(f"  [DELETE domain] {email.from_[:40]}")
            fetcher.delete_email(email.uid)
            result['action'] = 'deleted'
            result['reason'] = f"Delete domain: {', '.join(domains)}"
            return result

        # 7. Check delete keywords (matches subject OR body)
        if self.delete_filter.should_delete(email.subject, email.text):
            keywords = self.delete_filter.get_matching_keywords(email.subject, email.text)
            print(f"  [DELETE keywords] {email.subject[:40]}")
            fetcher.delete_email(email.uid)
            result['action'] = 'deleted'
            result['reason'] = f"Delete keywords: {', '.join(keywords)}"
            return result

        # 8. No match - keep email
        result['action'] = 'keep'
        return result

    def _summarize_email(self, email: EmailMessage) -> str:
        """Summarize email with priority: Local AI (Notebook/Ollama) -> Configured Cloud -> Fallbacks."""
        try:
            email_data = {
                'from': email.from_,
                'subject': email.subject,
                'body': email.text or email.html
            }
            # Small delay
            time.sleep(1)
            
            # --- Tier 1: Local AI (Primary - Ubuntu) ---
            if self.config.ai.provider.lower() == "ollama" or self.config.localai.enabled:
                print(f"  [Tier 1] Trying Ubuntu AI at {self.ollama_summarizer.url}...")
                summary = self.ollama_summarizer.summarize(email_data)
                if not summary.startswith("[Error:") and not summary.startswith("[Ollama error"):
                    return summary
                print(f"  [Tier 1 Failed] {summary[:60]}...")

            # --- Tier 2: Local AI (Secondary - Windows) ---
            if self.windows_summarizer:
                print(f"  [Tier 2] Trying Windows AI at {self.windows_summarizer.url}...")
                summary = self.windows_summarizer.summarize(email_data)
                if not summary.startswith("[Error:") and not summary.startswith("[Ollama error"):
                    return summary
                print(f"  [Tier 2 Failed] {summary[:60]}...")

            # --- Tier 3: Configured Cloud Provider ---
            if self.config.ai.provider.lower() != "ollama":
                print(f"  [Cloud] Trying {self.config.ai.provider}...")
                summary = self.summarizer.summarize(email_data)
                
                # Smart Retry for Rate Limiting (429)
                if "429" in summary or "Too Many Requests" in summary:
                    print("  [Rate Limit] Cloud AI quota hit. Waiting 45s...")
                    time.sleep(45)
                    summary = self.summarizer.summarize(email_data)
                
                if not summary.startswith("[Error:") and not summary.startswith("[Could not summarize"):
                    return summary

            # --- Tier 3: Cloud Fallback Chain (NVIDIA, Gemini, etc.) ---
            print("  [Secondary Fallbacks] Trying NVIDIA/Gemini...")
            
            # Fallback Layer 1: NVIDIA
            if self.config.nvidia.api_key:
                nvidia = NvidiaSummarizer(api_key=self.config.nvidia.api_key, model="moonshotai/kimi-k2.5")
                summary = nvidia.summarize(email_data)
                if not summary.startswith("[Error:"): return summary

            # Fallback Layer 2: Gemini
            if self.config.gemini.api_key:
                gemini = GeminiSummarizer(api_key=self.config.gemini.api_key, model="gemini-2.0-flash")
                summary = gemini.summarize(email_data)
                if not summary.startswith("[Error:"): return summary
            
            return summary
        except Exception as e:
            print(f"  [Summarization error] {str(e)[:50]}")
            return f"[Could not summarize: {str(e)[:30]}...]"

    def _is_trusted(self, sender: str) -> bool:
        """Check if sender is trusted using cached list."""
        if not self.trusted_senders:
            return False
            
        sender_lower = sender.lower()
        return any(t in sender_lower for t in self.trusted_senders)

    def _load_trusted_senders(self) -> List[str]:
        """Load trusted senders from file once."""
        trusted_file = os.path.join(self.base_path, 'trusted_senders.txt')
        if not os.path.exists(trusted_file):
            return []

        try:
            with open(trusted_file, 'r', encoding='utf-8') as f:
                return [line.strip().lower() for line in f if line.strip()]
        except Exception as e:
            print(f"Error loading trusted senders: {e}")
            return []


def main():
    """Main entry point."""
    print("="*50)
    print("Mail Agent - Email Automation System (v2.1 Source)")
    print("="*50)

    try:
        config = load_config()
        print("Configuration loaded successfully")

        agent = MailAgent(config)

        def run_workflow():
            """Execute one run of the agent and send report."""
            report = agent.run_once()
            print("\n" + "="*50)
            print("Summary Report")
            print("="*50)
            print(f"Total Newest Emails Scanned: {report['all_processed']}")
            print(f"  - Moved to Spam: {report['spam_count']}")
            print(f"  - Moved to Trash: {report['deleted_count']}")
            print(f"  - Summarized & Read: {report['summarized_count']}")
            print(f"  - Telegram messages: {len(report['summarized'])}")

            if config.report.daily_summary:
                print(f"\nSending report to Telegram...")
                if agent.telegram_sender.send_summary(report):
                    print("Report sent to Telegram")
                else:
                    print("Failed to send report!")

        if config.schedule.enabled:
            scheduler = Scheduler(config.schedule.interval_hours)
            scheduler.run(run_workflow)
        else:
            run_workflow()

    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
