"""Hugging Face Inference API summarizer."""
import requests
import time
from typing import Dict, Optional


class HuggingFaceSummarizer:
    def __init__(self, api_key: str, model: str = "zai-org/GLM-4.7-Flash:novita",
                 max_tokens: int = 300, temperature: float = 0.3):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        # The working endpoint discovered from the HF website
        self.api_url = "https://router.huggingface.co/v1/chat/completions"

    def summarize(self, email_data: Dict[str, str]) -> str:
        """Summarize an email using Hugging Face Inference API."""
        prompt = self._create_prompt(email_data)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenAI compatible payload
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a professional assistant. Summarize emails concisely in 2-3 sentences."},
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
                timeout=180 
            )
            
            if response.status_code != 200:
                print(f"  [HuggingFace Error] Status: {response.status_code}, Response: {response.text[:200]}")
            
            response.raise_for_status()

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                summary = result["choices"][0].get("message", {}).get("content")
                if summary is not None:
                    return summary.strip()
                else:
                    return "[Error: Empty content from Hugging Face]"
            else:
                return "[Error: No choices in Hugging Face response]"

        except requests.exceptions.RequestException as e:
            print(f"Error calling Hugging Face API: {e}")
            return f"[Error: Could not summarize - {str(e)[:50]}]"

    def _create_prompt(self, email_data: Dict[str, str]) -> str:
        """Create summarization prompt."""
        from_ = email_data.get('from', 'Unknown')
        subject = email_data.get('subject', 'No subject')
        body = email_data.get('body', '')
        body_preview = body[:1500] if len(body) > 1500 else body

        return f"Summarize this email:\nFrom: {from_}\nSubject: {subject}\nBody: {body_preview}"
