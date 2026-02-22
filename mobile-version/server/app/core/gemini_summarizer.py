"""Google Gemini API summarizer."""
import requests
from typing import Dict, Optional


class GeminiSummarizer:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash",
                 max_tokens: int = 300, temperature: float = 0.3):
        self.api_key = api_key
        # Clean model name
        if model.startswith("models/"):
            model = model.replace("models/", "")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        # Use v1beta for best compatibility with 2.0-flash
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def summarize(self, email_data: Dict[str, str]) -> str:
        """Summarize an email using Gemini API."""
        prompt = self._create_prompt(email_data)

        params = {"key": self.api_key}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "temperature": self.temperature
            }
        }

        try:
            response = requests.post(
                self.api_url,
                params=params,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"  [Gemini Error] Status: {response.status_code}, Response: {response.text[:200]}")
            
            response.raise_for_status()

            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                summary = result["candidates"][0]["content"]["parts"][0]["text"]
                return summary.strip()
            else:
                return "[Error: No response from Gemini]"

        except requests.exceptions.RequestException as e:
            print(f"Error calling Gemini API: {e}")
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
