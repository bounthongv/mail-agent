# AGENTS.md - Mail Agent Project Guidelines

## Project Overview
Mail Agent is a self-hosted email automation system that fetches, filters, and summarizes emails using AI providers.

## Build/Lint/Test Commands

### Installation
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Run main application
python src\main.py

# Run with virtual environment
venv\Scripts\python.exe src\main.py
```

### Testing
```bash
# Run system verification test
python test_system.py

# Run mobile config test
python mobile-version\test_config.py

# Run specific test (single file)
python -m pytest test_system.py -v

# Run specific test function
python -c "from test_system import test_config; test_config()"
```

### Build (PyInstaller)
```bash
# Build executable
pyinstaller MailAgent.spec

# Or use build script
python build_new.py
```

## Code Style Guidelines

### Python Version
- **Python 3.8+** required
- Use type hints for function parameters and return values
- Prefer `pathlib` over `os.path` for new code

### Imports
```python
# Standard library imports first
import os
import sys
from typing import List, Dict, Optional

# Third-party imports
import yaml
import requests

# Local imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_loader import load_config
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `MailAgent`, `OpenRouterSummarizer`)
- **Functions**: snake_case (e.g., `load_config`, `summarize_email`)
- **Variables**: snake_case (e.g., `api_key`, `max_tokens`)
- **Constants**: UPPER_CASE (e.g., `DEFAULT_TIMEOUT`)
- **Private methods**: Leading underscore (e.g., `_load_trusted_senders`)

### Type Hints
Always use type hints:
```python
def load_config(config_dir: str = "config") -> AppConfig:
def summarize(self, email_data: Dict[str, str]) -> str:
def _is_trusted(self, sender: str) -> bool:
```

### Error Handling
```python
try:
    result = operation()
except SpecificException as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    return default_value
except Exception as e:
    print(f"Unexpected error: {e}")
    return None
```

### Configuration Files
- Settings: `config/settings.yaml`
- Credentials: `config/credentials.yaml` (git-ignored)
- Patterns: `config/patterns/*.txt`

### Project Structure
```
src/
├── main.py                    # Entry point
├── config_loader.py           # Config dataclasses
├── scheduler.py               # Scheduling logic
├── email_handler/
│   └── fetcher.py            # Email fetching via IMAP
├── filters/                   # Spam/delete filters
│   ├── domain_filter.py
│   ├── keyword_filter.py
│   └── ...
├── summarizer/               # AI summarization
│   ├── openrouter_summarizer.py
│   ├── gemini_summarizer.py
│   └── ...
└── reports/
    └── telegram_sender.py    # Telegram integration
```

### Key Patterns
- **Dataclasses** for configuration objects
- **Filter classes** with `is_spam()` / `should_delete()` methods
- **Summarizer classes** with `summarize()` method returning string
- **Error messages** prefixed with `[Error: ...]` or `[Component error]`

### Environment Detection
```python
# Check if running from PyInstaller executable
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(__file__)
```

### Testing Guidelines
- Use `test_*.py` naming convention
- Test functions should start with `test_`
- Include assertions for validation
- Print status with `[OK]` prefix for success

### Dependencies
- imap-tools>=0.5.0
- PyYAML>=6.0
- requests>=2.31.0
- python-telegram-bot>=20.0
- torch, transformers (for local AI)

### Security Notes
- Never commit credentials.yaml
- Use App Passwords for Gmail (not regular passwords)
- API keys should be in credentials.yaml, not hardcoded
- Pattern files in config/patterns/ can contain sensitive info

### AI Provider Priority
1. Local AI (Ollama/Qwen) - Primary
2. Cloud providers (OpenRouter, Gemini, DeepSeek, etc.)
3. Fallback chain (NVIDIA → Gemini → HuggingFace → OpenRouter)

### File Patterns
All pattern files in `config/patterns/`:
- One pattern per line
- Case-insensitive matching
- Empty lines ignored
- No wildcards (exact match or substring search)
