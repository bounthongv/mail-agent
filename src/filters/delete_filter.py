"""Delete immediately pattern filter."""
from typing import List


def load_patterns(filepath: str) -> List[str]:
    """Load delete keyword patterns from file."""
    if not filepath:
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip().lower() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        return []


class DeleteFilter:
    def __init__(self, delete_keywords_file: str):
        self.delete_keywords = load_patterns(delete_keywords_file)

    def should_delete(self, subject: str, body: str) -> bool:
        """Check if subject OR body contains delete keywords."""
        content = f"{subject} {body}".lower()

        for keyword in self.delete_keywords:
            if keyword in content:
                return True
        return False

    def get_matching_keywords(self, subject: str, body: str) -> List[str]:
        """Return matching delete keywords."""
        content = f"{subject} {body}".lower()
        return [k for k in self.delete_keywords if k in content]
