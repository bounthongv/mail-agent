"""NVIDIA NIM API summarizer (OpenAI compatible)."""
import requests
from typing import Dict, Optional


class NvidiaSummarizer:
    def __init__(self, api_key: str, model: str = "moonshotai/kimi-k2.5",
                 max_tokens: int = 300, temperature: float = 0.3):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    def summarize(self, email_data: Dict[str, str]) -> str:
        """Summarize an email using NVIDIA NIM API."""
        prompt = self._create_prompt(email_data)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional assistant. Summarize the following email in 2-3 concise sentences."},
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
                timeout=300
            )
            
            if response.status_code != 200:
                print(f"  [NVIDIA Error] Status: {response.status_code}, Response: {response.text[:200]}")
            
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                summary = result["choices"][0].get("message", {}).get("content")
                if summary is not None:
                    return summary.strip()
                else:
                    return "[Error: Empty content from NVIDIA]"
            else:
                return "[Error: No choices in NVIDIA response]"

        except requests.exceptions.RequestException as e:
            print(f"Error calling NVIDIA API: {e}")
            return f"[Error: Could not summarize - {str(e)[:50]}]"

    def _create_prompt(self, email_data: Dict[str, str]) -> str:
        """Create summarization prompt."""
        from_ = email_data.get('from', 'Unknown')
        subject = email_data.get('subject', 'No subject')
        body = email_data.get('body', '')

        body_preview = body[:1500] if len(body) > 1500 else body

        prompt = f"""Summarize this email:
From: {from_}
Subject: {subject}
Body: {body_preview}

Summary:"""

        return prompt
