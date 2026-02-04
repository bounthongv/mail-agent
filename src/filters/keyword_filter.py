"""Keyword-based spam filter."""
from typing import List


def load_patterns(filepath: str) -> List[str]:
    """Load keyword patterns from file."""
    if not filepath:
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        return []


class KeywordFilter:
    def __init__(self, spam_keywords_file: str):
        self.spam_keywords = load_patterns(spam_keywords_file)

    def is_spam(self, subject: str, body: str) -> bool:
        """Check if subject OR body contains spam keywords."""
        content = f"{subject} {body}".lower()

        for keyword in self.spam_keywords:
            if keyword in content:
                return True
        return False

    def get_matching_keywords(self, subject: str, body: str) -> List[str]:
        """Return matching spam keywords."""
        content = f"{subject} {body}".lower()
        return [k for k in self.spam_keywords if k in content]
