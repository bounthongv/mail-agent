"""OpenRouter API summarizer with retry logic."""
import requests
import time
from typing import Dict, Optional


class OpenRouterSummarizer:
    def __init__(self, api_key: str, model: str = "z-ai/glm-4.5-air:free",
                 max_tokens: int = 300, temperature: float = 0.3,
                 max_retries: int = 3, initial_delay: int = 2):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def summarize(self, email_data: Dict[str, str]) -> str:
        """Summarize an email using OpenRouter API with retry logic."""
        prompt = self._create_prompt(email_data)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mail-agent.local",
            "X-Title": "Mail Agent"
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

        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload,
                    timeout=60  # Increased timeout
                )

                if response.status_code == 429:
                    # Rate limited - wait and retry
                    delay = self.initial_delay * (2 ** attempt)
                    print(f"  Rate limited, retrying in {delay}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue

                response.raise_for_status()

                result = response.json()
                summary = result["choices"][0]["message"]["content"]
                return summary.strip()

            except requests.exceptions.RequestException as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    delay = self.initial_delay * (2 ** attempt)
                    print(f"  API error: {last_error[:50]}, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                print(f"Error calling OpenRouter API after {self.max_retries} attempts: {last_error}")
                return f"[Error: Could not summarize - {last_error[:50]}]"

        error_msg = last_error if last_error else "Rate limit exceeded"
        return f"[Error: Could not summarize - {error_msg}]"

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
