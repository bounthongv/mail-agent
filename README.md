# Mail Agent

Self-hosted email automation system that fetches, filters, and summarizes emails.

## Features

- **Multiple Email Accounts**: Support for multiple email accounts via IMAP
- **Spam Filtering**: Domain, email, and keyword-based spam detection
- **Auto-Delete**: Move unwanted emails to Trash
- **AI Summarization**: Uses OpenRouter API to summarize important emails
- **Telegram Reports**: Daily summary reports sent to Telegram
- **Configurable Scheduling**: Set run interval via configuration

## How It Works

For each unread email, the system applies filters in this order:

```
1. trusted_senders.txt    → SKIP (keep unread, don't process)
2. spam_emails.txt        → MOVE TO SPAM folder (exact email match)
3. spam_domains.txt       → MOVE TO SPAM folder (domain match)
4. spam_keywords.txt      → MOVE TO SPAM folder (subject/body keywords)
5. delete_emails.txt      → MOVE TO TRASH (exact email match)
6. delete_domains.txt     → MOVE TO TRASH (domain match)
7. delete_keywords.txt    → MOVE TO TRASH (subject/body keywords)
8. Remaining emails       → SUMMARIZE and send to Telegram
```

## Pattern Files

All pattern files are in `config/patterns/` directory.

| File | Purpose | Example |
|------|---------|---------|
| `trusted_senders.txt` | Always keep these senders | `boss@company.com` |
| `spam_emails.txt` | Exact emails → Spam | `noreply@ads.com` |
| `spam_domains.txt` | Domains → Spam | `marketing-ads.com` |
| `spam_keywords.txt` | Keywords → Spam | `buy now`, `limited offer` |
| `delete_emails.txt` | Exact emails → Trash | `unsub@newsletter.com` |
| `delete_domains.txt` | Domains → Trash | `spam-advertiser.com` |
| `delete_keywords.txt` | Keywords → Trash | `unsubscribe`, `opt-out` |

## Pattern File Format

Each file contains one pattern per line. Text is case-insensitive.

### trusted_senders.txt
```
boss@company.com
family@gmail.com
friend@yahoo.com
```

### spam_emails.txt (exact email match)
```
noreply@marketing.com
unsubscribe@ads.com
promo@deals.com
```

### spam_domains.txt (domain matching)
```
spam-domain.com
marketing-ads.com
clickbait.net
```

### spam_keywords.txt (matches subject OR body)
```
buy now
limited offer
winner
click here
free money
act now
```

### delete_emails.txt (exact email match)
```
unsub@newsletter.com
optout@promos.com
```

### delete_domains.txt (domain matching)
```
spam-advertiser.com
daily-deals.xyz
```

### delete_keywords.txt (matches subject OR body)
```
unsubscribe
opt-out
remove from list
stop receiving
cancel subscription
```

## Quick Start

### 1. Gmail App Password Required

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification**
3. Go to https://myaccount.google.com/apppasswords
4. Create App Password (16 characters)
5. Update `config/credentials.yaml`

### 2. Run the System

```bash
cd D:\mail-agent
.\venv\Scripts\activate
python src\main.py
```

The system will run every 6 hours (configurable).

## Configuration

### config/settings.yaml
- `schedule.interval_hours` - Run frequency (default: 6 hours)
- `ai.model` - AI model for summarization
- `report.max_emails_per_report` - Max emails per report

### config/credentials.yaml (git-ignored)
- Email accounts with IMAP credentials
- Telegram bot token and chat ID
- OpenRouter API key

## Telegram Setup

1. Get Chat ID: Search @userinfobot on Telegram
2. Create Bot: Talk to @BotFather
   - `/newbot` - Create bot
   - `/token` - Get token
3. Update credentials.yaml

## Project Structure

```
mail-agent/
├── config/
│   ├── settings.yaml
│   ├── credentials.yaml
│   └── patterns/
│       ├── trusted_senders.txt
│       ├── spam_emails.txt
│       ├── spam_domains.txt
│       ├── spam_keywords.txt
│       ├── delete_emails.txt
│       ├── delete_domains.txt
│       └── delete_keywords.txt
├── src/
│   ├── config_loader.py
│   ├── main.py
│   ├── email_handler/
│   │   └── fetcher.py
│   ├── filters/
│   │   ├── domain_filter.py
│   │   ├── keyword_filter.py
│   │   ├── delete_filter.py
│   │   ├── delete_domain_filter.py
│   │   ├── delete_email_filter.py
│   │   └── spam_email_filter.py
│   ├── summarizer/
│   │   └── openrouter_summarizer.py
│   ├── reports/
│   │   └── telegram_sender.py
│   └── scheduler.py
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.8+
- Gmail with App Password OR other IMAP email
- OpenRouter API key
- Telegram account

## License

MIT
