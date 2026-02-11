"""xAI Grok API summarizer."""
import requests
from typing import Dict, Optional


class GrokSummarizer:
    def __init__(self, api_key: str, model: str = "grok-beta",
                 max_tokens: int = 300, temperature: float = 0.3):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api_url = "https://api.x.ai/v1/chat/completions"

    def summarize(self, email_data: Dict[str, str]) -> str:
        """Summarize an email using Grok API."""
        prompt = self._create_prompt(email_data)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that summarizes emails concisely."},
                {"role": "user", "content": prompt}
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
            
            if response.status_code != 200:
                print(f"  [Grok Error] Status: {response.status_code}, Response: {response.text[:200]}")
            
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                summary = result["choices"][0]["message"]["content"]
                return summary.strip()
            else:
                return "[Error: No response from Grok]"

        except requests.exceptions.RequestException as e:
            print(f"Error calling Grok API: {e}")
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
