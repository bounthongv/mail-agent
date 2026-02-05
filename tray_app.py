"""System tray application for Mail Agent."""
import sys
import os
import threading
import pystray
from PIL import Image, ImageDraw
from pystray import MenuItem as item
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, filedialog
import time
import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_loader import load_config
from src.main import MailAgent
from src.scheduler import Scheduler


class DebugLogWindow:
    """Debug log viewer window."""
    
    def __init__(self, log_entries):
        self.window = tk.Tk()
        self.window.title("Mail Agent - Debug Log")
        self.window.geometry("900x600")
        self.log_entries = log_entries
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create log viewer widgets."""
        # Title
        title = tk.Label(
            self.window,
            text="🐛 Mail Agent Debug Log",
            font=('Arial', 12, 'bold'),
            bg='#2c3e50',
            fg='white'
        )
        title.pack(fill='x', padx=10, pady=10)
        
        # Controls
        controls_frame = tk.Frame(self.window)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        # Clear button
        clear_btn = tk.Button(
            controls_frame,
            text="Clear Log",
            command=self.clear_log,
            bg='#dc3545',
            fg='white'
        )
        clear_btn.pack(side='left', padx=5)
        
        # Save button
        save_btn = tk.Button(
            controls_frame,
            text="Save Log",
            command=self.save_log,
            bg='#28a745',
            fg='white'
        )
        save_btn.pack(side='left', padx=5)
        
        # Refresh button
        refresh_btn = tk.Button(
            controls_frame,
            text="Refresh",
            command=self.refresh_log,
            bg='#17a2b8',
            fg='white'
        )
        refresh_btn.pack(side='left', padx=5)
        
        # Text widget for log display
        log_frame = tk.Frame(self.window)
        log_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollable text
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#333333',
            height=20
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Status label
        self.status_label = tk.Label(
            self.window,
            text=f"Log entries: {len(self.log_entries)}",
            font=('Arial', 10),
            fg='gray'
        )
        self.status_label.pack(fill='x', padx=10, pady=5)
        
        # Load log entries
        self.refresh_log()
        
    def refresh_log(self):
        """Refresh the log display."""
        self.log_text.delete('1.0', tk.END)
        
        if self.log_entries:
            for entry in reversed(self.log_entries):  # Show newest first
                # Color code based on level
                if "[ERROR]" in entry:
                    self.log_text.insert('1.0', entry + '\n', 'error')
                elif "[INFO]" in entry:
                    self.log_text.insert('1.0', entry + '\n', 'info')
                else:
                    self.log_text.insert('1.0', entry + '\n', 'normal')
        
        self.status_label.config(text=f"Log entries: {len(self.log_entries)}")
        
        # Configure text colors
        self.log_text.tag_config('error', foreground='#dc3545')
        self.log_text.tag_config('info', foreground='#17a2b8')
    
    def clear_log(self):
        """Clear the log."""
        if messagebox.askyesno("Clear Log", "Clear all log entries?"):
            self.log_entries.clear()
            self.log_text.delete('1.0', tk.END)
            self.status_label.config(text="Log entries: 0")
    
    def save_log(self):
        """Save log to file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mail_agent_debug_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for entry in self.log_entries:
                    f.write(entry + '\n')
            
            messagebox.showinfo("Success", f"Log saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")


class MailAgentTray:
    def __init__(self):
        self.config = None
        self.agent = None
        self.scheduler_thread = None
        self.is_running = False
        self.is_paused = False
        self.icon = None
        self.debug_log = []
        self.max_log_entries = 500
        
        # Load config
        try:
            self.config = load_config()
            self.agent = MailAgent(self.config)
            self.add_log("✓ Application started", "INFO")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
            sys.exit(1)

    def create_image(self):
        """Create tray icon image."""
        # Create a simple envelope icon
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='white')
        dc = ImageDraw.Draw(image)
        
        # Draw envelope
        dc.rectangle([10, 20, 54, 44], fill='lightblue', outline='blue', width=2)
        dc.polygon([10, 20, 32, 35, 54, 20], fill='lightblue', outline='blue')
        
        return image

    def show_about(self):
        """Show about dialog."""
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "About Mail Agent",
            "Mail Agent\n\n"
            "Automated Email Management System\n\n"
            "By: Dr. Bounthong Vongxaya\n"
            "Mobile/WhatsApp: 020 91316541\n\n"
            "Version: 1.0.0"
        )
        root.destroy()

    def add_log(self, message: str, level: str = "INFO"):
        """Add entry to debug log."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.debug_log.append(log_entry)
        
        # Keep only last N entries
        if len(self.debug_log) > self.max_log_entries:
            self.debug_log = self.debug_log[-self.max_log_entries:]
        
        # Also print to console
        print(log_entry)

    def show_debug_log(self):
        """Show debug log window."""
        DebugLogWindow(self.debug_log)
        """Show configuration window."""
        ConfigWindow(self)

    def show_configure(self):
        """Show configuration window."""
        ConfigWindow(self)

    def toggle_pause(self):
        """Toggle pause/resume."""
        self.is_paused = not self.is_paused
        status = "PAUSED" if self.is_paused else "RESUMED"
        self.add_log(f"⏸ {status}", "INFO")
        self.update_menu()

    def update_menu(self):
        """Update menu items."""
        if self.icon:
            self.icon.menu = self.create_menu()

    def create_menu(self):
        """Create context menu."""
        pause_text = "Resume" if self.is_paused else "Pause"
        return pystray.Menu(
            item('About', self.show_about),
            item('Configure', self.show_configure),
            item('Debug Log', self.show_debug_log),
            item(pause_text, self.toggle_pause),
            item('Exit', self.exit_app)
        )

    def run_scheduler(self):
        """Run the mail agent scheduler in background."""
        self.add_log("🚀 Mail Agent started in system tray", "INFO")
        
        while self.is_running:
            if not self.is_paused:
                try:
                    self.add_log("🔍 Starting email check...", "INFO")
                    report = self.agent.run_once()
                    
                    stats = []
                    stats.append(f"✅ Processed: {report['all_processed']}")
                    stats.append(f"🚫 Spam: {report['all_spam_count']}")
                    stats.append(f"🗑️ Deleted: {report['all_deleted_count']}")
                    stats.append(f"📊 Unread: {report['processed']}")
                    stats.append(f"📧 Summarized: {report['summarized_count']}")
                    
                    self.add_log("📊 Email check results: " + " | ".join(stats), "INFO")
                    
                    if self.config.report.daily_summary and report['summarized_count'] > 0:
                        self.add_log("📤 Sending report to Telegram...", "INFO")
                        success = self.agent.telegram_sender.send_summary(report)
                        status = "✅ Sent" if success else "❌ Failed"
                        self.add_log(f"📤 Telegram report: {status}", "INFO" if success else "ERROR")
                        
                except Exception as e:
                    error_msg = f"❌ Error during email check: {e}"
                    self.add_log(error_msg, "ERROR")
            
            # Wait for next run
            interval = self.config.schedule.interval_hours * 3600
            for _ in range(interval):
                if not self.is_running:
                    break
                time.sleep(1)

    def start(self):
        """Start the tray application."""
        self.is_running = True
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # Create and run tray icon
        self.icon = pystray.Icon(
            "mail_agent",
            self.create_image(),
            "Mail Agent",
            menu=self.create_menu()
        )
        
        self.icon.run()

    def exit_app(self):
        """Exit the application."""
        self.add_log("🛑 Application exiting...", "INFO")
        self.is_running = False
        if self.icon:
            self.icon.stop()
        sys.exit(0)


class ConfigWindow:
    """Configuration window for editing pattern files."""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Tk()
        self.window.title("Mail Agent Configuration")
        self.window.geometry("800x600")
        
        # Pattern files
        self.patterns_dir = os.path.join(os.path.dirname(__file__), 'config', 'patterns')
        self.pattern_files = {
            'Trusted Senders': 'trusted_senders.txt',
            'Spam Emails': 'spam_emails.txt',
            'Spam Domains': 'spam_domains.txt',
            'Spam Keywords': 'spam_keywords.txt',
            'Delete Emails': 'delete_emails.txt',
            'Delete Domains': 'delete_domains.txt',
            'Delete Keywords': 'delete_keywords.txt'
        }
        
        self.create_widgets()
        self.window.mainloop()
    
    def create_widgets(self):
        """Create configuration widgets."""
        # Title
        title = tk.Label(
            self.window,
            text="Mail Agent Configuration",
            font=('Arial', 14, 'bold')
        )
        title.pack(pady=10)
        
        # Tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Email Accounts Tab
        self.create_email_tab(notebook)
        
        # Telegram Tab
        self.create_telegram_tab(notebook)
        
        # AI Settings Tab
        self.create_ai_tab(notebook)
        
        # Pattern files tabs
        self.text_widgets = {}
        for name, filename in self.pattern_files.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=name)
            
            # Instructions
            info = tk.Label(
                frame,
                text=f"One entry per line. Changes are saved automatically.",
                font=('Arial', 9),
                fg='gray'
            )
            info.pack(pady=5)
            
            # Text editor
            text_widget = scrolledtext.ScrolledText(
                frame,
                wrap=tk.WORD,
                font=('Consolas', 10)
            )
            text_widget.pack(fill='both', expand=True, padx=10, pady=5)
            
            # Load content
            filepath = os.path.join(self.patterns_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    text_widget.insert('1.0', f.read())
            
            self.text_widgets[filename] = text_widget
        
        # Buttons
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        save_btn = tk.Button(
            button_frame,
            text="Save All Settings",
            command=self.save_all,
            bg='#4CAF50',
            fg='white',
            padx=20,
            pady=5
        )
        save_btn.pack(side='left', padx=5)
        
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy,
            padx=20,
            pady=5
        )
        close_btn.pack(side='left', padx=5)
    
    def create_email_tab(self, notebook):
        """Create email accounts configuration tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Email Accounts")
        
        # Instructions
        info = tk.Label(
            frame,
            text="Add Gmail accounts with App Passwords (enable 2FA first)",
            font=('Arial', 9),
            fg='blue'
        )
        info.pack(pady=5)
        
        # Email list frame
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Listbox with scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.email_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=6)
        self.email_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.email_listbox.yview)
        
        # Buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Add Email", command=self.add_email).pack(side='left', padx=2)
        tk.Button(btn_frame, text="Remove", command=self.remove_email).pack(side='left', padx=2)
        
        # Load existing emails
        self.load_emails()
    
    def create_telegram_tab(self, notebook):
        """Create Telegram configuration tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Telegram")
        
        # Instructions
        info = tk.Label(
            frame,
            text="Create bot at @BotFather and get Chat ID from @userinfobot",
            font=('Arial', 9),
            fg='blue'
        )
        info.pack(pady=5)
        
        # Bot Token
        tk.Label(frame, text="Bot Token:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.token_entry = tk.Entry(frame, width=60, show="*")
        self.token_entry.grid(row=0, column=1, padx=10, pady=5)
        
        # Chat ID
        tk.Label(frame, text="Chat ID:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.chat_id_entry = tk.Entry(frame, width=60)
        self.chat_id_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Test button
        tk.Button(frame, text="Test Connection", command=self.test_telegram).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Load existing settings
        self.load_telegram()
    
    def create_ai_tab(self, notebook):
        """Create AI configuration tab."""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="AI Settings")
        
        # AI Provider
        tk.Label(frame, text="AI Provider:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.ai_provider = ttk.Combobox(frame, values=["openrouter", "local", "gemini", "deepseek"], width=20)
        self.ai_provider.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        self.ai_provider.bind('<<ComboboxSelected>>', self.on_ai_provider_change)
        
        # API Key (for cloud providers)
        tk.Label(frame, text="API Key:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.api_key_entry = tk.Entry(frame, width=60, show="*")
        self.api_key_entry.grid(row=1, column=1, padx=10, pady=5)
        
        # Model
        tk.Label(frame, text="Model:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.model_entry = tk.Entry(frame, width=60)
        self.model_entry.grid(row=2, column=1, padx=10, pady=5)
        
        # Schedule
        tk.Label(frame, text="Check Interval (hours):").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.interval_entry = tk.Entry(frame, width=10)
        self.interval_entry.insert(0, "6")
        self.interval_entry.grid(row=3, column=1, sticky='w', padx=10, pady=5)
        
        # Load existing settings
        self.load_ai_settings()
    
    def on_ai_provider_change(self, event=None):
        """Handle AI provider change."""
        provider = self.ai_provider.get()
        if provider == "local":
            self.api_key_entry.config(state='disabled')
            self.model_entry.delete(0, 'end')
            self.model_entry.insert(0, "qwen2.5:3b")
        else:
            self.api_key_entry.config(state='normal')
            models = {
                "openrouter": "meta-llama/llama-3.2-3b-instruct:free",
                "gemini": "gemini-1.5-flash",
                "deepseek": "deepseek-chat"
            }
            self.model_entry.delete(0, 'end')
            self.model_entry.insert(0, models.get(provider, ""))
    
    def load_emails(self):
        """Load email accounts from config."""
        try:
            # Get config files path
            if getattr(sys, 'frozen', False):
                config_path = os.path.join(os.path.dirname(sys.executable), 'config')
            else:
                config_path = os.path.join(os.path.dirname(__file__), 'config')
            
            credentials_file = os.path.join(config_path, 'credentials.yaml')
            if os.path.exists(credentials_file):
                with open(credentials_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    self.email_listbox.delete(0, 'end')
                    for email in data.get('emails', []):
                        self.email_listbox.insert('end', f"{email['email']} ({'Enabled' if email.get('enabled') else 'Disabled'})")
        except Exception as e:
            print(f"Error loading emails: {e}")
    
    def load_telegram(self):
        """Load Telegram settings."""
        try:
            if getattr(sys, 'frozen', False):
                config_path = os.path.join(os.path.dirname(sys.executable), 'config')
            else:
                config_path = os.path.join(os.path.dirname(__file__), 'config')
            
            credentials_file = os.path.join(config_path, 'credentials.yaml')
            if os.path.exists(credentials_file):
                with open(credentials_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    telegram = data.get('telegram', {})
                    self.token_entry.insert(0, telegram.get('bot_token', ''))
                    self.chat_id_entry.insert(0, str(telegram.get('chat_id', '')))
        except Exception as e:
            print(f"Error loading telegram: {e}")
    
    def load_ai_settings(self):
        """Load AI settings."""
        try:
            if getattr(sys, 'frozen', False):
                config_path = os.path.join(os.path.dirname(sys.executable), 'config')
            else:
                config_path = os.path.join(os.path.dirname(__file__), 'config')
            
            settings_file = os.path.join(config_path, 'settings.yaml')
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    ai = data.get('ai', {})
                    self.ai_provider.set(ai.get('provider', 'openrouter'))
                    self.model_entry.insert(0, ai.get('model', ''))
                    
                    # Load API key based on provider
                    credentials_file = os.path.join(config_path, 'credentials.yaml')
                    if os.path.exists(credentials_file):
                        with open(credentials_file, 'r', encoding='utf-8') as f:
                            creds = yaml.safe_load(f)
                            if self.ai_provider.get() == 'openrouter':
                                self.api_key_entry.insert(0, creds.get('openrouter', {}).get('api_key', ''))
                            elif self.ai_provider.get() == 'gemini':
                                self.api_key_entry.insert(0, creds.get('gemini', {}).get('api_key', ''))
                            elif self.ai_provider.get() == 'deepseek':
                                self.api_key_entry.insert(0, creds.get('deepseek', {}).get('api_key', ''))
                    
                    schedule = data.get('schedule', {})
                    self.interval_entry.insert(0, str(schedule.get('interval_hours', 6)))
        except Exception as e:
            print(f"Error loading AI settings: {e}")
    
    def add_email(self):
        """Add email account dialog."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Email Account")
        dialog.geometry("400x200")
        
        tk.Label(dialog, text="Email:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        email_entry = tk.Entry(dialog, width=40)
        email_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Password:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        pass_entry = tk.Entry(dialog, width=40, show="*")
        pass_entry.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Gmail App Password\n(Enable 2FA first)").grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        
        def save():
            if email_entry.get() and pass_entry.get():
                emails = []
                for i in range(self.email_listbox.size()):
                    entry = self.email_listbox.get(i)
                    emails.append({'email': entry.split(' ')[0], 'password': '', 'imap_host': 'imap.gmail.com', 'imap_port': 993, 'enabled': True})
                
                emails.append({
                    'email': email_entry.get(),
                    'password': pass_entry.get(),
                    'imap_host': 'imap.gmail.com',
                    'imap_port': 993,
                    'enabled': True
                })
                
                # Update listbox
                self.email_listbox.insert('end', f"{email_entry.get()} (Enabled)")
                dialog.destroy()
        
        tk.Button(dialog, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=10)
    
    def remove_email(self):
        """Remove selected email."""
        selection = self.email_listbox.curselection()
        if selection:
            self.email_listbox.delete(selection[0])
    
    def test_telegram(self):
        """Test Telegram connection."""
        token = self.token_entry.get()
        chat_id = self.chat_id_entry.get()
        
        if not token or not chat_id:
            tk.messagebox.showerror("Error", "Please enter bot token and chat ID")
            return
        
        try:
            bot = Bot(token=token)
            bot.send_message(chat_id=int(chat_id), text="✅ Mail Agent test message - Configuration working!")
            tk.messagebox.showinfo("Success", "Test message sent to Telegram!")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to send test message:\n{e}")
    
    def save_all(self):
        """Save all settings including patterns, emails, telegram, and AI."""
        try:
            # Get config path
            if getattr(sys, 'frozen', False):
                config_path = os.path.join(os.path.dirname(sys.executable), 'config')
            else:
                config_path = os.path.join(os.path.dirname(__file__), 'config')
            
            os.makedirs(config_path, exist_ok=True)
            
            # Save pattern files
            for filename, text_widget in self.text_widgets.items():
                filepath = os.path.join(config_path, 'patterns', filename)
                content = text_widget.get('1.0', 'end-1c')
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Save emails, telegram, and AI settings
            credentials_file = os.path.join(config_path, 'credentials.yaml')
            settings_file = os.path.join(config_path, 'settings.yaml')
            
            # Build credentials data
            emails = []
            for i in range(self.email_listbox.size()):
                entry = self.email_listbox.get(i)
                email = entry.split(' ')[0]
                emails.append({
                    'email': email,
                    'password': 'REPLACE_WITH_ACTUAL_PASSWORD',  # Users must edit manually
                    'imap_host': 'imap.gmail.com',
                    'imap_port': 993,
                    'enabled': True
                })
            
            credentials = {
                'emails': emails,
                'telegram': {
                    'bot_token': self.token_entry.get(),
                    'chat_id': int(self.chat_id_entry.get()) if self.chat_id_entry.get() else 0
                },
                'openrouter': {'api_key': self.api_key_entry.get()},
                'gemini': {'api_key': self.api_key_entry.get()},
                'deepseek': {'api_key': self.api_key_entry.get()}
            }
            
            settings = {
                'schedule': {
                    'enabled': True,
                    'interval_hours': int(self.interval_entry.get()) if self.interval_entry.get() else 6
                },
                'ai': {
                    'provider': self.ai_provider.get(),
                    'model': self.model_entry.get(),
                    'max_tokens': 300,
                    'temperature': 0.3
                },
                'localai': {
                    'enabled': True,
                    'provider': 'qwen',
                    'model': 'qwen2.5:3b'
                },
                'report': {
                    'daily_summary': True,
                    'max_emails_per_report': 20
                }
            }
            
            # Save files
            with open(credentials_file, 'w', encoding='utf-8') as f:
                yaml.dump(credentials, f, default_flow_style=False)
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                yaml.dump(settings, f, default_flow_style=False)
            
            messagebox.showinfo("Success", "All settings saved!\n\n⚠️ Important: Email passwords need to be set manually in credentials.yaml for security.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")


def main():
    """Main entry point."""
    app = MailAgentTray()
    app.start()


if __name__ == "__main__":
    main()
