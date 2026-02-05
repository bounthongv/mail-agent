# Mail Agent - Quick Start Guide

## What is Mail Agent?

Mail Agent is a smart email assistant that runs quietly in your system tray and:
- ✅ Automatically filters spam emails
- ✅ Deletes unwanted emails  
- ✅ Summarizes important emails with AI
- ✅ Sends you daily reports on Telegram
- ✅ Shows real-time debug logs ⭐

## Installation (First Time)

1. **Extract the files**
   - Unzip `MailAgent.zip` to any folder
   - Example: `C:\MailAgent` or Desktop

2. **Run the application**
   - Double-click `MailAgent.exe`
   - A small envelope icon (📧) appears in your system tray (bottom-right corner)
   - That's it! The app is now running in the background

## Daily Use

### Finding the App
- Look for the envelope icon (📧) in your system tray
- If you don't see it, click the ^ arrow to show hidden icons

### Context Menu Options
Right-click envelope icon (📧) to see:

| Menu Item | What it Does |
|-----------|--------------|
| **About** | Shows version and author info |
| **Configure** | Opens pattern editor (see below) |
| **Debug Log** | Opens real-time activity log |
| **Pause** | Stops email checking temporarily |
| **Exit** | Closes the application |

### Debug Log Viewer ⭐ *NEW*
Right-click tray icon → **Debug Log** to:
- ✅ See real-time activity (last 500 entries)
- ✅ Color-coded by level (INFO=green, ERROR=red)
- ✅ **Clear Log** button to reset
- ✅ **Save Log** button to export to file
- ✅ **Refresh** button to update
- ✅ Automatic scrolling to newest entries

### Status Indicator
The app runs continuously and checks emails every 6 hours automatically. You'll see:
- 📊 Telegram notifications with summaries
- 🐛 Debug log shows all activities
- ⏸ Visual indicator when paused

## Configuring Email Filters

### Accessing Configuration
1. Right-click envelope icon
2. Select **Configure**
3. Use tabs to edit patterns
4. Click **Save All** when done

### Pattern Files

#### Trusted Senders
Emails from these addresses are **never filtered**
```
boss@company.com
family@gmail.com
```

#### Spam Emails
These exact emails go to **Spam folder**
```
marketing@spam.com
ads@promotional.com
```

#### Spam Domains
All emails from these domains go to **Spam**
```
spam-domain.com
marketing-ads.com
```

#### Spam Keywords
Emails with these words go to **Spam**
```
buy now
limited offer
click here
```

#### Delete Emails
These exact emails go to **Trash**
```
newsletter@example.com
```

#### Delete Domains
All emails from these domains go to **Trash**
```
daily-deals.com
```

#### Delete Keywords
Emails with these words go to **Trash**
```
unsubscribe
opt-out
remove from list
```

### Pattern Rules
- ✅ One entry per line
- ✅ Case-insensitive
- ✅ No special formatting needed
- ✅ Exact or partial matches work

## Understanding Reports

Every 6 hours, you'll receive a Telegram message with:

```
📧 Email Processing Report
===================================
📊 Total Emails Scanned: 150
  • Moved to Spam: 3
  • Moved to Trash: 12

📬 Unread Emails: 5
  • Spam: 0
  • Deleted: 2
  • Summarized: 3

✨ Email Summaries:
1. From: project@company.com
   Subject: Project Update Required
   This is an automated acknowledgment confirming receipt of your project update request.

2. From: security@bank.com
   Subject: Security Alert
   A new login was detected on your account requiring immediate attention.

🕐 2026-02-04 19:30:15
```

### Report Sections
- **Total Scanned**: All emails checked during the run
- **Spam/Deleted**: Emails moved to respective folders
- **Unread Processing**: Only newly received emails
- **Summaries**: AI-generated summaries of important emails
- **Timestamp**: When the report was generated

## Tips & Best Practices

### Daily Operation
✅ **Start on boot**: Create a shortcut in Startup folder  
✅ **Pause before vacation**: Right-click → Pause  
✅ **Check Telegram**: Open app for your daily summaries  
✅ **Monitor Debug Log**: See exactly what the app is doing

### Pattern Management
✅ **Start conservative**: Add a few patterns, monitor results, then expand  
✅ **Review summaries**: Check what's being filtered vs summarized  
✅ **Use Debug Log**: If emails aren't processed correctly, check the log  

### Troubleshooting

| Problem | Solution |
|---------|----------|
| No tray icon | Check Task Manager → MailAgent.exe running? |
| No Telegram messages | Right-click → Configure → Check Telegram settings |
| Emails not filtering | Right-click → Debug Log → Check for errors |
| App doesn't start | Run as Administrator (first time) |

## Advanced Options

### Email Accounts
Add multiple email accounts in `config/credentials.yaml`:
```yaml
emails:
  - email: "work@company.com"
    password: "app_password"
    enabled: true
  - email: "personal@gmail.com"
    password: "another_password"
    enabled: true
```

### Scheduling
Change check frequency in `config/settings.yaml`:
```yaml
schedule:
  enabled: true
  interval_hours: 6  # Any number from 1 to 24
```

### AI Model Selection
Available options in `config/settings.yaml`:
- GLM-4.5-Air (free, good summaries)
- Gemini Flash (free, fast)
- DeepSeek (free, good quality)

## Author

**Dr. Bounthong Vongxaya**  
Mobile/WhatsApp: 020 91316541

---

## 🎉 Enjoy Your Clean Inbox!

Your Mail Agent is now actively protecting your inbox, automatically filtering unwanted emails and providing you with concise summaries of what matters most.

**Questions?** Send me a message!