"""Exact email spam filter."""
from typing import List


def load_patterns(filepath: str) -> List[str]:
    """Load email patterns from file."""
    if not filepath:
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        return []


class SpamEmailFilter:
    def __init__(self, spam_emails_file: str):
        self.spam_emails = load_patterns(spam_emails_file)

    def is_spam(self, sender: str) -> bool:
        """Check if sender email is in spam list."""
        sender_lower = sender.lower()
        for email in self.spam_emails:
            if email == sender_lower:
                return True
        return False

    def get_matching_emails(self, sender: str) -> List[str]:
        """Return matching spam emails."""
        sender_lower = sender.lower()
        return [e for e in self.spam_emails if e == sender_lower]
