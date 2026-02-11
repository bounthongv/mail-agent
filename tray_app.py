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
import io

# Add src to path
# Add base directory to path
if getattr(sys, 'frozen', False):
    # PyInstaller bundled environment
    base_dir = sys._MEIPASS
else:
    # Normal python environment
    base_dir = os.path.dirname(os.path.abspath(__file__))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.config_loader import load_config
from src.main import MailAgent
from src.scheduler import Scheduler


class LogRedirector:
    """Redirects stdout/stderr to the tray app log."""
    def __init__(self, log_func):
        self.log_func = log_func
        self.buffer = ""

    def write(self, message):
        try:
            # Prevent recursion - if we're already processing a write, just buffer
            if hasattr(self, '_writing') and self._writing:
                # Just add to buffer without processing
                message = message.replace('\r\n', '\n').replace('\r', '\n')
                self.buffer += message
                return len(message)
            
            self._writing = True
            try:
                # Buffer the message to handle multi-line output properly
                # Replace carriage returns with newlines for consistent processing
                message = message.replace('\r\n', '\n').replace('\r', '\n')
                self.buffer += message

                # Process complete lines
                while '\n' in self.buffer:
                    line, self.buffer = self.buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        # Only add to log, don't print again to avoid duplication
                        self.log_func(line, "INFO")

                return len(message)
            finally:
                self._writing = False
        except Exception:
            # Silently ignore any errors during logging to prevent hangs
            return len(message) if 'message' in locals() else 0

    def flush(self):
        try:
            # Flush any remaining buffer content
            # Use a flag to prevent recursion during flush
            if hasattr(self, '_flushing') and self._flushing:
                return
            self._flushing = True
            try:
                if self.buffer.strip():
                    buffer_content = self.buffer.strip()
                    self.buffer = ""  # Clear buffer first to prevent recursion
                    self.log_func(buffer_content, "INFO")
            finally:
                self._flushing = False
        except Exception:
            # Silently ignore any errors during flush to prevent hangs
            pass


class EditPatternsWindow:
    """Window for editing pattern .txt files only."""

    def __init__(self, parent=None):
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()
            self.window.withdraw()  # Hide until needed
        self.window.title("Edit Filter Patterns")
        self.window.geometry("700x500")
        self.window.transient()  # Set as transient to avoid taskbar issues

        # Determine the correct patterns directory based on whether running from source or executable
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running from source
            base_dir = os.path.dirname(os.path.abspath(__file__))
        self.patterns_dir = os.path.join(base_dir, 'config', 'patterns')

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
        
    def create_widgets(self):
        # Tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.text_widgets = {}
        for name, filename in self.pattern_files.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=name)
            
            # Instructions
            tk.Label(frame, text=f"Edit {filename} (one per line)", font=('Arial', 9, 'italic')).pack(pady=5)
            
            # Text editor
            text_widget = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=('Consolas', 10))
            text_widget.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Load content
            filepath = os.path.join(self.patterns_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        text_widget.insert('1.0', f.read())
                except Exception as e:
                    text_widget.insert('1.0', f"Error loading file: {e}")
            
            self.text_widgets[filename] = text_widget
            
        # Buttons
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Save Patterns", bg='#28a745', fg='white', 
                  command=self.save_patterns, padx=15).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Close", command=self.window.destroy, padx=15).pack(side='left', padx=5)

    def save_patterns(self):
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.patterns_dir, exist_ok=True)

            for filename, text_widget in self.text_widgets.items():
                filepath = os.path.join(self.patterns_dir, filename)
                content = text_widget.get('1.0', 'end-1c').strip()
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
            messagebox.showinfo("Success", "Patterns saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save patterns: {e}")


class DebugLogWindow:
    """Debug log viewer window."""

    def __init__(self, log_entries, parent=None, config=None):
        self.log_entries = log_entries
        self.parent = parent
        self.config = config
        if parent:
            self.window = tk.Toplevel(parent)
        else:
            self.window = tk.Tk()
            self.window.withdraw()
        self.window.title("Mail Agent - Debug Log")
        self.window.geometry("900x600")
        self.window.transient()

        # Track the last entry count to detect new entries
        self.last_entry_count = len(log_entries)

        self.create_widgets()

        # Start auto-refresh timer
        self.auto_refresh()
        
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
                elif any(keyword in entry for keyword in ["[SPAM]", "[DELETED]", "[TRUSTED]", "[SUMMARY]", "[OLD]", "[PASS]"]):
                    # Special keywords for email processing
                    self.log_text.insert('1.0', entry + '\n', 'special')
                elif any(keyword in entry for keyword in ["=", "-", "✅", "🚫", "📧", "📊", "📤", "🔍", "🚀", "🐛", "💡", "⏸", "🛑", "▶️"]):
                    # Special formatting for status indicators
                    self.log_text.insert('1.0', entry + '\n', 'status')
                else:
                    self.log_text.insert('1.0', entry + '\n', 'normal')

        self.status_label.config(text=f"Log entries: {len(self.log_entries)}")

        # Configure text colors
        self.log_text.tag_config('error', foreground='#dc3545')
        self.log_text.tag_config('info', foreground='#17a2b8')
        self.log_text.tag_config('special', foreground='#ff8c00')  # Orange for email processing
        self.log_text.tag_config('status', foreground='#28a745')   # Green for status indicators
    
    def clear_log(self):
        """Clear the log."""
        if messagebox.askyesno("Clear Log", "Clear all log entries?"):
            self.log_entries.clear()
            self.log_text.delete('1.0', tk.END)
            self.status_label.config(text="Log entries: 0")
    
    def auto_refresh(self):
        """Auto-refresh the log display when new entries are detected."""
        current_count = len(self.log_entries)
        if current_count != self.last_entry_count:
            self.refresh_log()
            self.last_entry_count = current_count

            # Scroll to bottom to show latest entries
            self.log_text.see(tk.END)

        # Schedule next check in 1 second
        self.window.after(1000, self.auto_refresh)

    def save_log(self):
        """Save log to file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mail_agent_debug_{timestamp}.txt"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for entry in self.log_entries:
                    f.write(entry + '\n')

            # Also save a more detailed version with all the processing information
            detailed_filename = f"mail_agent_detailed_{timestamp}.txt"
            with open(detailed_filename, 'w', encoding='utf-8') as f:
                f.write("MAIL AGENT DETAILED DEBUG LOG\n")
                f.write("="*50 + "\n")
                f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*50 + "\n\n")

                for entry in self.log_entries:
                    f.write(entry + '\n')

            messagebox.showinfo("Success", f"Logs saved to {filename} and {detailed_filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save log: {e}")


class MailAgentTray:
    def __init__(self):
        self.config = None
        self.agent = None
        self.scheduler_thread = None
        self.is_running = False
        self.is_paused = True  # Start paused to allow configuration first
        self.icon = None
        self.debug_log = []
        self.max_log_entries = 2000
        
        # Capture original stdout/stderr for logging to avoid recursion
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Create hidden root window for managing dialogs
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the root window
        
        # Define paths
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_patterns_path = os.path.join(self.base_dir, 'config', 'patterns')
        
        # Load config
        try:
            self.config = load_config()

            # Redirect during agent initialization to capture any startup prints
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            redirector = LogRedirector(self.add_log)
            sys.stdout = redirector
            sys.stderr = redirector

            self.agent = MailAgent(self.config)

            # Restore original stdout/stderr after initialization
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            try:
                redirector.flush()
            except Exception:
                # Ignore flush errors to prevent hangs
                pass

            # Add startup messages similar to source version
            self.add_log("="*50, "INFO")
            self.add_log("Mail Agent - Email Automation System (v2.6 Compiled)", "INFO")
            self.add_log("="*50, "INFO")
            self.add_log("Configuration loaded successfully", "INFO")
            self.add_log(f"Using {self.config.ai.provider.upper()} AI", "INFO")
            self.add_log(f"Scheduler started. Interval: {self.config.schedule.interval_hours} hours", "INFO")

            self.add_log("🔧 Mail Agent started - PAUSED (Right-click to configure)", "INFO")
            self.add_log("💡 Right-click tray icon → Start when ready", "INFO")
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
        def _show():
            messagebox.showinfo(
                "About Mail Agent",
                "Mail Agent\n\n"
                "Automated Email Management System\n\n"
                "By: Dr. Bounthong Vongxaya\n"
                "Mobile/WhatsApp: 020 91316541\n\n"
                "Version: 1.0.0"
            )
        self.root.after(0, _show)

    def add_log(self, message: str, level: str = "INFO"):
        """Add entry to debug log."""
        try:
            # Handle multi-line messages by splitting them
            lines = message.split('\n')
            for line in lines:
                line = line.strip()
                if line:  # Only log non-empty lines
                    # Check if the message already contains a timestamp to avoid duplication
                    if not line.startswith('[') or '] [' not in line:
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_entry = f"[{timestamp}] [{level}] {line}"
                    else:
                        # Message already has timestamp/formatting, use as-is
                        log_entry = line

                    self.debug_log.append(log_entry)

                    # Keep only last N entries
                    if len(self.debug_log) > self.max_log_entries:
                        self.debug_log = self.debug_log[-self.max_log_entries:]

                    # Also print to console - use original_stdout to avoid recursion
                    if self.original_stdout:
                        try:
                            self.original_stdout.write(log_entry + '\n')
                            self.original_stdout.flush()
                        except Exception:
                            pass
        except Exception as e:
            # Silently ignore logging errors to prevent hangs
            import sys
            try:
                sys.__stderr__.write(f"Error in add_log: {e}\n")
            except:
                pass

    def show_debug_log(self):
        """Show debug log window."""
        self.root.after(0, lambda: DebugLogWindow(self.debug_log, self.root, self.config))

    def show_edit_patterns(self):
        """Show the simplified pattern editor."""
        self.root.after(0, lambda: EditPatternsWindow(self.root))

    def toggle_pause(self):
        """Toggle pause/resume."""
        was_paused = self.is_paused
        self.is_paused = not self.is_paused

        if self.is_paused:
            status = "PAUSED"
            action = "STOPPED"
            self.add_log(f"⏸️ {action} - Email processing paused", "INFO")
        else:
            status = "RESUMED"
            action = "STARTED"
            self.add_log(f"▶️ {action} - Email processing {status.lower()}", "INFO")

        self.update_menu()

    def update_menu(self):
        """Update menu items."""
        if self.icon:
            self.icon.menu = self.create_menu()

    def create_menu(self):
        """Create context menu."""
        pause_text = "Start Processing" if self.is_paused else "Pause Processing"
        return pystray.Menu(
            item('About', self.show_about),
            item('Edit Patterns', self.show_edit_patterns),
            item('View Debug Log', self.show_debug_log),
            item(pause_text, self.toggle_pause),
            item('Exit', self.exit_app)
        )

    def run_scheduler(self):
        """Run the mail agent scheduler in background."""
        self.add_log("🚀 Mail Agent started in system tray", "INFO")

        # Print initial startup information similar to source version
        self.add_log("="*50, "INFO")
        self.add_log("Mail Agent - Email Automation System (v2.6 Compiled)", "INFO")
        self.add_log("="*50, "INFO")
        self.add_log("Configuration loaded successfully", "INFO")
        self.add_log(f"Using {self.config.ai.provider.upper()} AI", "INFO")
        self.add_log(f"Scheduler started. Interval: {self.config.schedule.interval_hours} hours", "INFO")

        while self.is_running:
            if self.is_paused:
                time.sleep(1)
                continue

            # Run processing
            try:
                # Redirect stdout/stderr to capture agent's print statements
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                redirector = LogRedirector(self.add_log)
                sys.stdout = redirector
                sys.stderr = redirector

                try:
                    print("🔍 Starting email check...")

                    # Run the email processing with timeout to prevent hanging
                    import threading
                    report_result = [None]
                    processing_exception = [None]
                    timed_out = [False]

                    def run_processing():
                        try:
                            # Define callback to check if we should stop
                            def check_stop():
                                return self.is_paused or not self.is_running

                            report_result[0] = self.agent.run_once(check_stop=check_stop)
                        except Exception as e:
                            processing_exception[0] = e

                    processing_thread = threading.Thread(target=run_processing)
                    processing_thread.daemon = True
                    processing_thread.start()
                    processing_thread.join(timeout=1800)  # 30 minute timeout for entire processing

                    if processing_thread.is_alive():
                        print("⚠️ Email processing timed out after 30 minutes")
                        # Mark as timed out to skip the rest of the processing
                        timed_out[0] = True
                    elif processing_exception[0]:
                        print(f"❌ Error during email processing: {processing_exception[0]}")
                        raise processing_exception[0]
                    else:
                        report = report_result[0]

                        stats = []
                        stats.append(f"✅ Scanned: {report['all_processed']}")
                        stats.append(f"🚫 Spam: {report['spam_count']}")
                        stats.append(f"🗑️ Deleted: {report['deleted_count']}")
                        stats.append(f"📧 Summarized: {report['summarized_count']}")

                        print(f"📊 Results: " + " | ".join(stats))

                    # Only send Telegram report if processing completed successfully and not timed out
                    if not timed_out[0] and self.config.report.daily_summary and report['summarized_count'] > 0:
                        print("📤 Sending report to Telegram...")

                        result = [None]
                        exception_occurred = [None]

                        def send_report():
                            try:
                                result[0] = self.agent.telegram_sender.send_summary(report)
                            except Exception as e:
                                exception_occurred[0] = e

                        thread = threading.Thread(target=send_report)
                        thread.daemon = True
                        thread.start()
                        thread.join(timeout=30)  # 30 second timeout

                        if thread.is_alive():
                            print("📤 Telegram report: ⏳ Timeout")
                        elif exception_occurred[0]:
                            print(f"📤 Telegram report: ❌ Error - {exception_occurred[0]}")
                        else:
                            success = result[0]
                            status = "✅ Sent" if success else "❌ Failed"
                            print(f"📤 Telegram report: {status}")

                finally:
                    # Always restore streams and flush any remaining buffer
                    redirector.flush()
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr

                    # Print completion status after restoring stdout/stderr to ensure it's always logged
                    if 'timed_out' in locals() and timed_out[0]:
                        self.add_log(f"⚠️ Processing timed out at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
                    else:
                        self.add_log(f"✅ Processing completed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
                    next_run_time = datetime.datetime.now() + datetime.timedelta(hours=self.config.schedule.interval_hours)
                    self.add_log(f"⏰ Next run scheduled at: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')} (in {self.config.schedule.interval_hours} hours)", "INFO")

            except Exception as e:
                # Restore original stdout temporarily to ensure exception is logged
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                # Capture exceptions
                error_msg = f"❌ Error during email check: {e}"
                self.add_log(error_msg, "ERROR")
                import traceback
                self.add_log(traceback.format_exc(), "ERROR")

            # Wait for next run
            interval = self.config.schedule.interval_hours * 3600
            next_run_time = datetime.datetime.now() + datetime.timedelta(hours=self.config.schedule.interval_hours)
            self.add_log(f"⏳ Waiting {self.config.schedule.interval_hours}h for next run (until {next_run_time.strftime('%Y-%m-%d %H:%M:%S')})...", "INFO")

            for _ in range(interval):
                if not self.is_running:
                    break
                # If user pauses during wait, break loop to enter pause state
                if self.is_paused:
                    self.add_log("⏸ Schedule interrupted by pause", "INFO")
                    break
                time.sleep(1)

    def start(self):
        """Start the tray application."""
        self.is_running = True
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # Create tray icon
        self.icon = pystray.Icon(
            "mail_agent",
            self.create_image(),
            "Mail Agent",
            menu=self.create_menu()
        )
        
        # Run tray icon in a separate thread so tkinter can own the main thread
        threading.Thread(target=self.icon.run, daemon=True).start()
        
        # Start the hidden root window's main loop
        self.root.mainloop()

    def exit_app(self):
        """Exit the application."""
        self.add_log("🛑 Application exiting...", "INFO")
        self.is_running = False
        if self.icon:
            self.icon.stop()
        self.root.quit()
        sys.exit(0)


def main():
    """Main entry point."""
    app = MailAgentTray()
    app.start()


if __name__ == "__main__":
    main()
