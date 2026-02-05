"""Email fetching module using imap-tools."""
from imap_tools import MailBox, AND
from typing import List, Optional, Callable
from dataclasses import dataclass
import socket


@dataclass
class EmailMessage:
    uid: str
    subject: str
    from_: str
    text: str
    html: str
    date: str


class EmailFetcher:
    def __init__(self, email: str, password: str, imap_host: str, imap_port: int, timeout: int = 60):
        self.email = email
        self.password = password
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.timeout = timeout
        self.mailbox: Optional[MailBox] = None

    def connect(self):
        """Connect to IMAP server with timeout."""
        # Set socket timeout to prevent hanging
        socket.setdefaulttimeout(self.timeout)
        self.mailbox = MailBox(self.imap_host, self.imap_port)
        self.mailbox.login(self.email, self.password)
        print(f"Connected to {self.email}")

    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.mailbox:
            try:
                self.mailbox.logout()
                print(f"Disconnected from {self.email}")
            except Exception as e:
                print(f"Disconnected from {self.email} (forced: {e})")
            finally:
                self.mailbox = None

    def fetch_unread(self, folder: str = "INBOX") -> List[EmailMessage]:
        """Fetch unread emails only."""
        if not self.mailbox:
            self.connect()

        emails = []
        self.mailbox.folder.set(folder)

        for msg in self.mailbox.fetch(AND(seen=False), limit=50, reverse=True):
            email_msg = self._parse_message(msg)
            emails.append(email_msg)

        return emails

    def fetch_all(self, folder: str = "INBOX", limit: int = 100, progress_callback: Optional[Callable[[int], None]] = None) -> List[EmailMessage]:
        """Fetch ALL emails (read and unread) with configurable limit and progress tracking."""
        if not self.mailbox:
            self.connect()

        emails = []
        self.mailbox.folder.set(folder)

        # Fetch emails with configurable limit (default 100 instead of 500)
        # mark_seen=False ensures we don't interfere with "unread" status for Step 2
        print(f"Fetching up to {limit} emails from {folder}...")
        for i, msg in enumerate(self.mailbox.fetch(limit=limit, reverse=True, mark_seen=False), 1):
            email_msg = self._parse_message(msg)
            emails.append(email_msg)
            
            # Report progress every 25 emails
            if progress_callback and i % 25 == 0:
                progress_callback(i)
            elif i % 25 == 0:
                print(f"  Fetched {i} emails...")

        print(f"Completed fetching {len(emails)} emails")
        return emails

    def _parse_message(self, msg) -> EmailMessage:
        """Parse IMAP message to EmailMessage dataclass."""
        # Use clean email address from from_values if available
        sender_email = msg.from_values.email if msg.from_values else msg.from_
        
        return EmailMessage(
            uid=str(msg.uid),
            subject=msg.subject or "",
            from_=sender_email or "",
            text=msg.text or "",
            html=msg.html or "",
            date=str(msg.date) if msg.date else ""
        )

    def move_to_spam(self, uid: str, folder: str = "INBOX"):
        """Move email to Spam folder."""
        if not self.mailbox:
            self.connect()

        try:
            self.mailbox.folder.set(folder)
            # Try common spam folder names
            spam_folders = ["[Gmail]/Spam", "Spam", "Junk", "Junk E-mail"]
            success = False
            
            for spam_folder in spam_folders:
                try:
                    self.mailbox.move(uid, spam_folder)
                    print(f"  [SUCCESS] Moved email {uid} to {spam_folder}")
                    success = True
                    break
                except Exception:
                    continue
            
            if not success:
                print(f"  [ERROR] Could not find a valid Spam folder for email {uid}")
        except Exception as e:
            print(f"  [ERROR] Failed to move email {uid} to Spam: {e}")

    def mark_as_read(self, uid: str, folder: str = "INBOX"):
        """Mark email as read."""
        if not self.mailbox:
            self.connect()

        try:
            self.mailbox.folder.set(folder)
            self.mailbox.flag(uid, [MailBox.FLAG_SEEN], True)
        except Exception as e:
            print(f"  [ERROR] Failed to mark email {uid} as read: {e}")

    def delete_email(self, uid: str, folder: str = "INBOX"):
        """Move email to Trash folder."""
        if not self.mailbox:
            self.connect()

        try:
            self.mailbox.folder.set(folder)
            # Try common trash folder names
            trash_folders = ["[Gmail]/Trash", "Trash", "Deleted Items", "Deleted"]
            success = False
            
            for trash_folder in trash_folders:
                try:
                    self.mailbox.move(uid, trash_folder)
                    print(f"  [SUCCESS] Moved email {uid} to {trash_folder}")
                    success = True
                    break
                except Exception:
                    continue
            
            if not success:
                # Fallback: mark as deleted if move fails
                self.mailbox.delete(uid)
                print(f"  [SUCCESS] Marked email {uid} as deleted (fallback)")
        except Exception as e:
            print(f"  [ERROR] Failed to delete email {uid}: {e}")
