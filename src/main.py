"""Mail Agent - Email Automation System.

Workflow:
1. Fetch ALL emails (read + unread) → Apply spam/delete filters
2. Fetch UNREAD emails only → Summarize and send to Telegram
"""

import os
import sys
import time
from datetime import datetime
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
from summarizer.local_summarizer import LocalSummarizer
from reports.telegram_sender import TelegramSender
from scheduler import Scheduler


class MailAgent:
    def __init__(self, config: AppConfig):
        self.config = config
        self.base_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'patterns')

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

        # Always initialize local summarizer as backup
        self.local_summarizer = LocalSummarizer(
            provider=config.localai.provider,
            model=config.localai.model
        )

        # Priority: OpenRouter (GLM-4.5-Air) -> Local AI (Qwen CLI) -> Gemini -> DeepSeek
        if config.ai.provider == "openrouter":
            print(f"Using OpenRouter API ({config.ai.model})")
            self.summarizer = OpenRouterSummarizer(
                api_key=config.openrouter.api_key,
                model=config.ai.model,
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
        elif config.ai.provider == "local" and config.localai.enabled:
            print(f"Using Local AI ({config.localai.provider})")
            self.summarizer = LocalSummarizer(
                provider=config.localai.provider,
                model=config.localai.model
            )
        elif config.gemini.api_key and config.gemini.api_key != "YOUR_GEMINI_API_KEY_HERE":
            print("Using Google Gemini API")
            self.summarizer = GeminiSummarizer(
                api_key=config.gemini.api_key,
                model="gemini-1.5-flash",
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
        elif config.deepseek.api_key and config.deepseek.api_key != "YOUR_DEEPSEEK_API_KEY_HERE":
            print("Using DeepSeek API (direct)")
            self.summarizer = DeepSeekSummarizer(
                api_key=config.deepseek.api_key,
                model="deepseek-chat",
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
        else:
            print("Using OpenRouter API (fallback)")
            self.summarizer = OpenRouterSummarizer(
                api_key=config.openrouter.api_key,
                model=config.ai.model,
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature
            )
        self.telegram_sender = TelegramSender(
            bot_token=config.telegram.bot_token,
            chat_id=config.telegram.chat_id
        )

    def run_once(self) -> Dict:
        """Run email processing once."""
        report = {
            'all_processed': 0,
            'all_spam_count': 0,
            'all_deleted_count': 0,
            'processed': 0,
            'spam_count': 0,
            'deleted_count': 0,
            'summarized_count': 0,
            'summarized': [],
            'spam_details': [],
            'deleted_details': [],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        for email_config in self.config.emails:
            if not email_config.enabled:
                print(f"Skipping disabled email: {email_config.email}")
                continue

            print(f"\n{'='*50}")
            print(f"Processing: {email_config.email}")
            print('='*50)

            fetcher = EmailFetcher(
                email=email_config.email,
                password=email_config.password,
                imap_host=email_config.imap_host,
                imap_port=email_config.imap_port,
                timeout=120  # 2 minutes timeout to prevent hanging
            )

            try:
                # STEP 1: Process ALL emails (read + unread) with spam/delete filters
                print("\n--- Step 1: Scanning ALL emails for spam/delete ---")
                # Reduce limit to 100 to prevent hanging on large inboxes
                all_emails = fetcher.fetch_all(limit=100)
                print(f"Found {len(all_emails)} total emails")

                for email in all_emails:
                    report['all_processed'] += 1
                    result = self._apply_filters(fetcher, email)

                    if result['action'] == 'spam':
                        report['all_spam_count'] += 1
                    elif result['action'] == 'deleted':
                        report['all_deleted_count'] += 1

                # STEP 2: Summarize only UNREAD emails
                print("\n--- Step 2: Summarizing UNREAD emails ---")
                unread_emails = fetcher.fetch_unread()
                print(f"Found {len(unread_emails)} unread emails")

                for i, email in enumerate(unread_emails):
                    print(f"\n[{i+1}/{len(unread_emails)}] Processing: {email.subject[:40]} from {email.from_[:30]}")
                    report['processed'] += 1
                    result = self._apply_filters(fetcher, email)
                    print(f"    Action: {result['action']}")

                    if result['action'] == 'spam':
                        report['spam_count'] += 1
                        report['spam_details'].append({
                            'from': email.from_,
                            'subject': email.subject,
                            'reason': result['reason']
                        })
                    elif result['action'] == 'deleted':
                        report['deleted_count'] += 1
                        report['deleted_details'].append({
                            'from': email.from_,
                            'subject': email.subject,
                            'reason': result['reason']
                        })
                    elif result['action'] == 'trusted':
                        # Trusted senders - summarize but don't apply filters
                        report['summarized_count'] += 1
                        summary = self._summarize_email(email)
                        if summary:
                            report['summarized'].append({
                                'account': email_config.email,  # Add email account
                                'from': email.from_,
                                'subject': email.subject,
                                'summary': summary
                            })
                    elif result['action'] == 'keep':
                        # Not matched any filter - summarize
                        print(f"  [SUMMARIZING] {email.subject[:40]}")
                        report['summarized_count'] += 1
                        summary = self._summarize_email(email)
                        print(f"  [SUMMARY] {summary[:50] if summary else 'EMPTY'}...")
                        if summary:
                            report['summarized'].append({
                                'account': email_config.email,  # Add email account
                                'from': email.from_,
                                'subject': email.subject,
                                'summary': summary
                            })

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
        """Summarize a single email with rate limiting and fallback."""
        try:
            email_data = {
                'from': email.from_,
                'subject': email.subject,
                'body': email.text or email.html
            }
            # Add delay to avoid rate limiting
            time.sleep(1)
            
            # Try primary summarizer
            summary = self.summarizer.summarize(email_data)
            
            # Fallback if primary fails
            if summary.startswith("[Error:") or summary.startswith("[Could not summarize"):
                print(f"  [Primary AI Failed] {summary}")
                print("  [FALLBACK] Trying Local AI...")
                fallback_summary = self.local_summarizer.summarize(email_data)
                if not fallback_summary.startswith("[Error") and not fallback_summary.startswith("[Qwen error"):
                    return fallback_summary
            
            return summary
        except Exception as e:
            print(f"  [Summarization error] {str(e)[:50]}")
            return f"[Could not summarize: {str(e)[:30]}...]"

    def _is_trusted(self, sender: str) -> bool:
        """Check if sender is trusted."""
        trusted_file = os.path.join(self.base_path, 'trusted_senders.txt')
        if not os.path.exists(trusted_file):
            return False

        with open(trusted_file, 'r', encoding='utf-8') as f:
            trusted = [line.strip().lower() for line in f if line.strip()]

        sender_lower = sender.lower()
        return any(t in sender_lower for t in trusted)


def main():
    """Main entry point."""
    print("="*50)
    print("Mail Agent - Email Automation System")
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
            print(f"All emails scanned: {report['all_processed']}")
            print(f"  - Moved to Spam: {report['all_spam_count']}")
            print(f"  - Moved to Trash: {report['all_deleted_count']}")
            print(f"Unread emails: {report['processed']}")
            print(f"  - Marked as spam: {report['spam_count']}")
            print(f"  - Deleted: {report['deleted_count']}")
            print(f"  - Summarized: {report['summarized_count']}")
            print(f"  - Telegram messages: {len(report['summarized'])}")
            print(f"  - Spam details: {len(report['spam_details'])}")
            print(f"  - Deleted details: {len(report['deleted_details'])}")

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
