"""Local AI Summarizer - Uses Qwen CLI or Ollama."""
import subprocess
import json
import os
from typing import Dict, Optional


class LocalSummarizer:
    def __init__(self, provider: str = "qwen", model: str = "qwen2.5:3b"):
        self.provider = provider  # "qwen" or "ollama"
        self.model = model

    def summarize(self, email_data: Dict[str, str]) -> str:
        """Summarize email using local CLI tool."""
        prompt = self._create_prompt(email_data)

        if self.provider == "qwen":
            return self._summarize_with_qwen(prompt)
        elif self.provider == "ollama":
            return self._summarize_with_ollama(prompt)
        else:
            return f"[Error: Unknown provider {self.provider}]"

    def _summarize_with_qwen(self, prompt: str) -> str:
        """Use Qwen CLI to summarize via npx."""
        try:
            # Get npx path
            npx_path = "C:\\Users\\Windows 10\\AppData\\Roaming\\npm\\npx.cmd"

            # Qwen Code CLI - use -p flag for prompt mode
            # Sanitize prompt to avoid command line issues
            clean_prompt = prompt.replace('"', "'").replace('\n', ' ')
            full_prompt = f"Summarize this email in 2-3 sentences: {clean_prompt}"

            # Use shell=True for npx on Windows, but pass command as string to avoid argument parsing issues
            # Or better: use shell=False with full path to npx.cmd
            result = subprocess.run(
                [npx_path, "@qwen-code/qwen-code", "-p", full_prompt],
                capture_output=True,
                text=True,
                timeout=90,
                shell=True # Kept shell=True but sanitized input
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return f"[Qwen error: {result.stderr[:100] if result.stderr else 'No output'}]"
        except Exception as e:
            return f"[Qwen error: {str(e)[:50]}]"

    def _summarize_with_ollama(self, prompt: str) -> str:
        """Use Ollama API to summarize."""
        try:
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                return f"[Ollama error: {response.status_code}]"
        except Exception as e:
            return f"[Ollama error: {str(e)[:50]}]"

    def _create_prompt(self, email_data: Dict[str, str]) -> str:
        """Create summarization prompt."""
        from_ = email_data.get('from', 'Unknown')
        subject = email_data.get('subject', 'No subject')
        body = email_data.get('body', '')

        body_preview = body[:1500] if len(body) > 1500 else body

        prompt = f"""Summarize this email in 2-3 short sentences:

From: {from_}
Subject: {subject}
Body: {body_preview}

Summary:"""

        return prompt

    def is_available(self) -> bool:
        """Check if the CLI tool is available."""
        try:
            if self.provider == "qwen":
                subprocess.run(["qwen", "--version"], capture_output=True, timeout=5)
                return True
            elif self.provider == "ollama":
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                return response.status_code == 200
        except:
            pass
        return False
