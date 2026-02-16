from imap_tools import MailBox, MailMessageFlags
import yaml

def check_msg_attrs():
    with open('config/credentials.yaml', 'r') as f:
        creds = yaml.safe_load(f)
    email_cfg = creds['emails'][0]
    
    with MailBox(email_cfg['imap_host']).login(email_cfg['email'], email_cfg['password']) as mailbox:
        print("Fetching with mark_seen=False, bulk=True...")
        for msg in mailbox.fetch(limit=50, reverse=True, mark_seen=False, bulk=True):
            if "Annisa" in msg.subject:
                print(f"Subject: {msg.subject[:50]}")
                print(f"Flags: {msg.flags}")
                is_seen = MailMessageFlags.SEEN in msg.flags
                print(f"Is Seen: {is_seen}")
                print("-" * 20)

if __name__ == "__main__":
    check_msg_attrs()
