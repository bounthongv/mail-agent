"""Configuration loader module."""
import os
import sys
import yaml
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmailConfig:
    email: str
    imap_host: str
    imap_port: int
    password: str
    enabled: bool


@dataclass
class TelegramConfig:
    bot_token: str
    chat_id: int


@dataclass
class OpenRouterConfig:
    api_key: str


@dataclass
class DeepSeekConfig:
    api_key: str


@dataclass
class GeminiConfig:
    api_key: str


@dataclass
class HuggingFaceConfig:
    api_key: str


@dataclass
class NvidiaConfig:
    api_key: str


@dataclass
class GroqConfig:
    api_key: str


@dataclass
class LocalAIConfig:
    enabled: bool
    provider: str  # "qwen" or "ollama"
    model: str


@dataclass
class ScheduleConfig:
    enabled: bool
    interval_hours: int


@dataclass
class AIConfig:
    provider: str
    model: str
    max_tokens: int
    temperature: float


@dataclass
class ReportConfig:
    daily_summary: bool
    max_emails_per_report: int


@dataclass
class AppConfig:
    schedule: ScheduleConfig
    ai: AIConfig
    report: ReportConfig
    emails: List[EmailConfig]
    telegram: TelegramConfig
    openrouter: OpenRouterConfig
    deepseek: DeepSeekConfig
    gemini: GeminiConfig
    huggingface: HuggingFaceConfig
    nvidia: NvidiaConfig
    groq: GroqConfig
    localai: LocalAIConfig


def load_pattern_file(filepath: str) -> List[str]:
    """Load patterns from text file, one per line."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def load_config(config_dir: str = "config") -> AppConfig:
    """Load configuration from YAML files."""
    # Check if running from executable (PyInstaller)
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        config_path = os.path.join(base_path, config_dir)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_path, "..", config_dir)

    settings_file = os.path.join(config_path, "settings.yaml")
    credentials_file = os.path.join(config_path, "credentials.yaml")

    with open(settings_file, 'r', encoding='utf-8') as f:
        settings = yaml.safe_load(f)

    with open(credentials_file, 'r', encoding='utf-8') as f:
        credentials = yaml.safe_load(f)

    schedule = ScheduleConfig(
        enabled=settings['schedule']['enabled'],
        interval_hours=settings['schedule']['interval_hours']
    )

    ai = AIConfig(
        provider=settings['ai']['provider'].strip(),
        model=settings['ai']['model'].strip(),
        max_tokens=settings['ai']['max_tokens'],
        temperature=settings['ai']['temperature']
    )

    report = ReportConfig(
        daily_summary=settings['report']['daily_summary'],
        max_emails_per_report=settings['report']['max_emails_per_report']
    )

    emails = [
        EmailConfig(
            email=e['email'],
            imap_host=e['imap_host'],
            imap_port=e['imap_port'],
            password=e['password'],
            enabled=e['enabled']
        )
        for e in credentials['emails']
    ]

    telegram = TelegramConfig(
        bot_token=credentials['telegram']['bot_token'],
        chat_id=credentials['telegram']['chat_id']
    )

    openrouter = OpenRouterConfig(
        api_key=credentials['openrouter']['api_key'].strip()
    )

    deepseek = DeepSeekConfig(
        api_key=credentials.get('deepseek', {}).get('api_key', '').strip()
    )

    gemini = GeminiConfig(
        api_key=credentials.get('gemini', {}).get('api_key', '').strip()
    )

    huggingface = HuggingFaceConfig(
        api_key=credentials.get('huggingface', {}).get('api_key', '').strip()
    )

    nvidia = NvidiaConfig(
        api_key=credentials.get('nvidia', {}).get('api_key', '').strip()
    )

    groq = GroqConfig(
        api_key=credentials.get('groq', {}).get('api_key', '').strip()
    )

    localai = LocalAIConfig(
        enabled=settings.get('localai', {}).get('enabled', False),
        provider=settings.get('localai', {}).get('provider', 'qwen'),
        model=settings.get('localai', {}).get('model', 'qwen2.5:3b')
    )

    return AppConfig(
        schedule=schedule,
        ai=ai,
        report=report,
        emails=emails,
        telegram=telegram,
        openrouter=openrouter,
        deepseek=deepseek,
        gemini=gemini,
        huggingface=huggingface,
        nvidia=nvidia,
        groq=groq,
        localai=localai
    )
