# Mail Agent - Project Context

## Project Overview
**Mail Agent** is a self-hosted email automation system designed to fetch, filter, and summarize emails. It connects to IMAP servers (like Gmail), applies user-defined filters to organize or delete emails, summarizes the remaining important emails using AI (OpenRouter, Gemini, DeepSeek, or LocalAI), and sends a daily digest report via Telegram.

## Key Features
- **Multi-Account Support**: Handles multiple IMAP email accounts.
- **Advanced Filtering**:
  - **Trusted Senders**: Skips processing for specific addresses.
  - **Spam/Delete**: filters based on exact email, domain, or keywords (subject/body).
  - **Actions**: Moves spam to the Spam folder and unwanted emails to Trash.
- **AI Summarization**: Supports multiple providers:
  - **OpenRouter** (default)
  - **Google Gemini**
  - **DeepSeek**
  - **Local AI** (via Qwen CLI)
- **Reporting**: Sends consolidated reports to a Telegram chat.
- **Scheduling**: Configurable run intervals (default: 6 hours).

## Architecture & Structure
The project follows a modular Python structure:

- **`src/`**: Source code
  - **`main.py`**: Entry point. Orchestrates the fetch -> filter -> summarize -> report workflow.
  - **`config_loader.py`**: Handles loading YAML configuration and pattern files.
  - **`scheduler.py`**: Manages the execution interval.
  - **`email_handler/`**: IMAP connection and fetching logic (`fetcher.py`).
  - **`filters/`**: Specialized classes for each filter type (domain, keyword, email, etc.).
  - **`summarizer/`**: Adapters for different AI APIs (`gemini_summarizer.py`, `openrouter_summarizer.py`, etc.).
  - **`reports/`**: Logic for formatting and sending Telegram messages (`telegram_sender.py`).
- **`config/`**: Configuration
  - **`settings.yaml`**: General app settings (schedule, AI provider, reporting).
  - **`credentials.yaml`**: (Git-ignored) Secrets like API keys and passwords.
  - **`patterns/`**: Text files defining filter rules (`spam_keywords.txt`, `trusted_senders.txt`, etc.).
- **`test_system.py`**: Simple script to verify configuration loading.
- **`requirements.txt`**: Python dependencies.

## Usage Guide

### Prerequisites
- Python 3.8+
- Active Virtual Environment (`venv`)
- `config/credentials.yaml` must be populated with:
  - IMAP details (Email/App Password)
  - AI API Key
  - Telegram Bot Token & Chat ID

### commands

**1. Run the Agent**
Execute the main script to start the scheduler (or run once depending on config):
```powershell
python src/main.py
```

**2. Verify Configuration**
Run the test script to ensure settings and patterns are loaded correctly:
```powershell
python test_system.py
```

**3. Manage Filters**
Edit the text files in `config/patterns/` to update filtering rules. Each line represents a new rule (case-insensitive).
- `trusted_senders.txt`
- `spam_emails.txt`, `spam_domains.txt`, `spam_keywords.txt`
- `delete_emails.txt`, `delete_domains.txt`, `delete_keywords.txt`

### Development Conventions
- **Code Style**: Standard Python PEP 8.
- **Error Handling**: The `main.py` loop includes try/except blocks to prevent one email account failure from crashing the entire agent.
- **Dependencies**: Managed via `pip` and `requirements.txt`.
