"""Mail Agent Setup Wizard."""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yaml

class SetupWizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mail Agent Setup")
        self.root.geometry("600x500")
        
        self.emails = []
        self.telegram_token = ""
        self.telegram_chat_id = ""
        
        self.create_ui()
    
    def create_ui(self):
        # Title
        title = tk.Label(self.root, text="Mail Agent Setup", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Frame for emails
        email_frame = ttk.LabelFrame(self.root, text="Email Accounts")
        email_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Email list
        self.email_listbox = tk.Listbox(email_frame, height=4)
        self.email_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Email buttons
        btn_frame = tk.Frame(email_frame)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Add Email", command=self.add_email).pack(side="left", padx=2)
        tk.Button(btn_frame, text="Remove", command=self.remove_email).pack(side="left", padx=2)
        
        # Telegram frame
        telegram_frame = ttk.LabelFrame(self.root, text="Telegram Bot")
        telegram_frame.pack(padx=10, pady=10, fill="x")
        
        tk.Label(telegram_frame, text="Bot Token:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.token_entry = tk.Entry(telegram_frame, width=50, show="*")
        self.token_entry.grid(row=0, column=1, padx=5, pady=2)
        
        tk.Label(telegram_frame, text="Chat ID:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.chat_id_entry = tk.Entry(telegram_frame, width=50)
        self.chat_id_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # AI selection
        ai_frame = ttk.LabelFrame(self.root, text="AI Service")
        ai_frame.pack(padx=10, pady=10, fill="x")
        
        self.ai_var = tk.StringVar(value="openrouter")
        tk.Radiobutton(ai_frame, text="OpenRouter API (Free)", variable=self.ai_var, value="openrouter").pack(anchor="w")
        tk.Radiobutton(ai_frame, text="Local Qwen CLI", variable=self.ai_var, value="local").pack(anchor="w")
        
        # Save buttons
        save_frame = tk.Frame(self.root)
        save_frame.pack(pady=10)
        
        tk.Button(save_frame, text="Save Configuration", command=self.save_config, 
                 bg="green", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(save_frame, text="Exit", command=self.root.quit).pack(side="left", padx=5)
        
        # Instructions
        instructions = """Instructions:
1. Add your Gmail accounts with App Passwords (not regular passwords)
2. Create a Telegram bot at @BotFather and get the token
3. Get your Chat ID from @userinfobot
4. Choose AI service (OpenRouter recommended)
5. Save configuration and run MailAgent.exe"""
        
        tk.Label(self.root, text=instructions, justify="left", font=("Arial", 9)).pack(padx=10, pady=5)
    
    def add_email(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Email Account")
        dialog.geometry("400x300")
        
        tk.Label(dialog, text="Email:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        email_entry = tk.Entry(dialog, width=40)
        email_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Password:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        pass_entry = tk.Entry(dialog, width=40, show="*")
        pass_entry.grid(row=1, column=1, padx=10, pady=5)
        
        tk.Label(dialog, text="Gmail App Password\n(Enable 2FA first)").grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        
        def save():
            if email_entry.get() and pass_entry.get():
                self.emails.append({
                    'email': email_entry.get(),
                    'password': pass_entry.get(),
                    'imap_host': 'imap.gmail.com',
                    'imap_port': 993,
                    'enabled': True
                })
                self.update_email_list()
                dialog.destroy()
        
        tk.Button(dialog, text="Save", command=save).grid(row=3, column=0, columnspan=2, pady=10)
    
    def remove_email(self):
        selection = self.email_listbox.curselection()
        if selection:
            index = selection[0]
            del self.emails[index]
            self.update_email_list()
    
    def update_email_list(self):
        self.email_listbox.delete(0, tk.END)
        for email in self.emails:
            self.email_listbox.insert(tk.END, email['email'])
    
    def save_config(self):
        if not self.emails:
            messagebox.showerror("Error", "Please add at least one email account")
            return
        
        token = self.token_entry.get()
        chat_id = self.chat_id_entry.get()
        
        if not token or not chat_id:
            messagebox.showerror("Error", "Please enter Telegram bot token and chat ID")
            return
        
        # Create config directory
        config_dir = "config"
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            os.makedirs(os.path.join(config_dir, "patterns"))
        
        # Save credentials
        credentials = {
            'emails': self.emails,
            'telegram': {
                'bot_token': token,
                'chat_id': int(chat_id)
            },
            'openrouter': {
                'api_key': 'YOUR_OPENROUTER_API_KEY_HERE'
            },
            'deepseek': {
                'api_key': 'YOUR_DEEPSEEK_API_KEY_HERE'
            },
            'gemini': {
                'api_key': 'YOUR_GEMINI_API_KEY_HERE'
            }
        }
        
        with open(os.path.join(config_dir, "credentials.yaml"), "w") as f:
            yaml.dump(credentials, f, default_flow_style=False)
        
        # Save settings
        settings = {
            'schedule': {'enabled': True, 'interval_hours': 6},
            'ai': {
                'provider': self.ai_var.get(),
                'model': 'meta-llama/llama-3.2-3b-instruct:free' if self.ai_var.get() == 'openrouter' else 'qwen2.5:3b',
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
        
        with open(os.path.join(config_dir, "settings.yaml"), "w") as f:
            yaml.dump(settings, f, default_flow_style=False)
        
        messagebox.showinfo("Success", "Configuration saved!\n\nYou can now run MailAgent.exe")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    wizard = SetupWizard()
    wizard.run()