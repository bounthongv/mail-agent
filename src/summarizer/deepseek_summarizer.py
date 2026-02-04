"""DeepSeek API summarizer - Direct API access."""
import requests
from typing import Dict, Optional


class DeepSeekSummarizer:
    def __init__(self, api_key: str, model: str = "deepseek-chat",
                 max_tokens: int = 300, temperature: float = 0.3):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api_url = "https://api.deepseek.com/chat/completions"

    def summarize(self, email_data: Dict[str, str]) -> str:
        """Summarize an email using DeepSeek API."""
        prompt = self._create_prompt(email_data)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            summary = result["choices"][0]["message"]["content"]
            return summary.strip()

        except requests.exceptions.RequestException as e:
            print(f"Error calling DeepSeek API: {e}")
            return f"[Error: Could not summarize - {str(e)[:50]}]"

    def _create_prompt(self, email_data: Dict[str, str]) -> str:
        """Create summarization prompt."""
        from_ = email_data.get('from', 'Unknown')
        subject = email_data.get('subject', 'No subject')
        body = email_data.get('body', '')

        body_preview = body[:1500] if len(body) > 1500 else body

        prompt = f"""Please summarize this email in 2-3 short sentences:

**From:** {from_}
**Subject:** {subject}

**Body:**
{body_preview}

**Summary:**"""

        return prompt

    def summarize_batch(self, emails: list) -> list:
        """Summarize multiple emails."""
        results = []
        for email in emails:
            summary = self.summarize(email)
            results.append({
                'from': email.get('from', 'Unknown'),
                'subject': email.get('subject', 'No subject'),
                'summary': summary
            })
        return results
