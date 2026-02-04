"""Domain-based spam filter."""
import re
from typing import List


def load_patterns(filepath: str) -> List[str]:
    """Load domain patterns from file."""
    if not filepath:
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        return []


def domain_matches(sender: str, pattern: str) -> bool:
    """Check if sender domain matches pattern (supports wildcards)."""
    sender_lower = sender.lower()
    pattern = pattern.lower()

    if pattern.startswith('*.'):
        suffix = pattern[2:]
        return sender_lower.endswith('.' + suffix) or sender_lower.endswith('@' + suffix)

    # Exact domain match (e.g. user@example.com matches example.com)
    if sender_lower.endswith('@' + pattern):
        return True
    
    # Subdomain match (e.g. user@sub.example.com matches example.com)
    if sender_lower.endswith('.' + pattern):
        return True

    return False


class DomainFilter:
    def __init__(self, spam_domains_file: str):
        self.spam_domains = load_patterns(spam_domains_file)

    def is_spam(self, sender: str) -> bool:
        """Check if sender domain is in spam list."""
        for domain in self.spam_domains:
            if domain_matches(sender, domain):
                return True
        return False

    def get_matching_domains(self, sender: str) -> List[str]:
        """Return matching spam domains."""
        return [d for d in self.spam_domains if domain_matches(sender, d)]
