"""Telegram report sender."""
from telegram import Bot
from telegram.error import TelegramError
from typing import Dict
import asyncio


class TelegramSender:
    def __init__(self, bot_token: str, chat_id: int):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_summary(self, report_data: Dict) -> bool:
        """Send summary report to Telegram (synchronous wrapper)."""
        message = self._format_message(report_data)
        
        try:
            if len(message) <= 4000:
                asyncio.run(self._send_async(message))
            else:
                # Split long message by lines to preserve formatting
                lines = message.split('\n')
                current_chunk = ""
                for line in lines:
                    if len(current_chunk) + len(line) + 1 > 4000:
                        asyncio.run(self._send_async(current_chunk))
                        current_chunk = line + "\n"
                    else:
                        current_chunk += line + "\n"
                if current_chunk:
                    asyncio.run(self._send_async(current_chunk))
            return True
        except Exception as e:
            print(f"Error sending to Telegram: {e}")
            return False

    async def _send_async(self, message: str):
        """Async implementation of sending message."""
        bot = Bot(token=self.bot_token)
        await bot.send_message(
            chat_id=self.chat_id,
            text=message,
            parse_mode='Markdown'
        )

    def _format_message(self, report_data: Dict) -> str:
        """Format report as Telegram message."""
        lines = []

        lines.append("👋 *Hi Boss!* This is the summary of my work on your mail today.")
        lines.append("📧 *Email Processing Report*")
        lines.append("=" * 35)
        
        # Overall scan results
        lines.append(f"\n*📊 Total Emails Scanned:* {report_data.get('all_processed', 0)}")
        lines.append(f"  • Moved to Spam: {report_data.get('spam_count', 0)}")
        lines.append(f"  • Moved to Trash: {report_data.get('deleted_count', 0)}")
        lines.append(f"  • Summarized: {report_data.get('summarized_count', 0)}")
        
        # Group by Account
        by_account = report_data.get('by_account', {})
        if by_account:
            for account_email, stats in by_account.items():
                if stats['processed'] == 0 and stats['summarized'] == 0 and stats['spam'] == 0 and stats['deleted'] == 0:
                    continue
                    
                lines.append("\n" + "=" * 35)
                lines.append(f"👤 *{account_email}*")
                lines.append(f"  • Scanned: {stats['processed']}")
                if stats['spam'] > 0: lines.append(f"  • Spam: {stats['spam']}")
                if stats['deleted'] > 0: lines.append(f"  • Deleted: {stats['deleted']}")
                if stats['summarized'] > 0: lines.append(f"  • Summaries: {stats['summarized']}")
                
                # Add summaries for this account
                if stats.get('summaries'):
                    lines.append("\n  *✨ Summaries:*")
                    for i, email in enumerate(stats['summaries'], 1):
                        lines.append(f"\n  *{i}. From:* `{email['from']}`")
                        lines.append(f"     *Sub:* _{email['subject']}_")
                        lines.append(f"     {email['summary']}")
        
        # Fallback for old format or if no account data
        elif report_data.get('summarized'):
            lines.append("\n" + "=" * 35)
            lines.append("\n*✨ All Summaries:*")
            for i, email in enumerate(report_data['summarized'], 1):
                account = email.get('account', 'Unknown')
                lines.append(f"\n*{i}.* Account: `{account}`")
                lines.append(f"From: `{email['from']}`")
                lines.append(f"Subject: _{email['subject']}_")
                lines.append(f"\n{email['summary']}")
        else:
            if not by_account:
                lines.append("\n_No new emails to summarize._")

        if report_data.get('spam_details'):
            lines.append("\n" + "=" * 35)
            lines.append("\n*🚫 Spam Details:*")
            for item in report_data['spam_details']:
                lines.append(f"\n• `{item['from']}`")
                lines.append(f"  Reason: {item['reason']}")

        if report_data.get('deleted_details'):
            lines.append("\n" + "=" * 35)
            lines.append("\n*🗑️ Deleted Details:*")
            for item in report_data['deleted_details']:
                lines.append(f"\n• `{item['from']}`")
                lines.append(f"  Reason: {item['reason']}")

        lines.append("\n" + "=" * 35)
        lines.append(f"🕐 _{report_data.get('timestamp', 'N/A')}_")

        return "\n".join(lines)

    def test_connection(self) -> bool:
        """Test bot connection."""
        try:
            asyncio.run(self._test_async())
            return True
        except Exception as e:
            print(f"Bot connection failed: {e}")
            return False

    async def _test_async(self):
        """Async implementation of connection test."""
        bot = Bot(token=self.bot_token)
        me = await bot.get_me()
        print(f"Bot connected: @{me.username}")