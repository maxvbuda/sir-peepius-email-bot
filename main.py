import base64
import imaplib
import smtplib
import email
import os
import json
import sys
import time
from flask import Flask, request
try:
    import functions_framework
except ImportError:
    functions_framework = None  # Will run in local mode
from email.utils import parseaddr
from email.mime.text import MIMEText
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file (for local) or environment (for Cloud)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TARGET_EMAILS_ENV = os.getenv("TARGET_EMAILS", "")
if not TARGET_EMAILS_ENV:
    print("❌ Missing TARGET_EMAILS in .env or environment.\nPlease set TARGET_EMAILS to a comma-separated list of addresses.")
    sys.exit(1)
TARGET_EMAILS = [e.strip() for e in TARGET_EMAILS_ENV.split(",") if e.strip()]

# Check secrets
for name, val in {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "EMAIL_USER": EMAIL_USER,
    "EMAIL_PASS": EMAIL_PASS,
}.items():
    if not val:
        print(f"❌ Missing {name} in .env — fix it first!")
        sys.exit(1)

IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def fetch_email_by_id(message_id):
    """Fetch a specific email by its Gmail message ID."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        # Search for the specific message
        _, data = mail.search(None, f"X-GM-MSGID {message_id}")
        
        if not data[0]:
            print(f"Message {message_id} not found")
            mail.logout()
            return None
        
        num = data[0].split()[0]
        _, msg_data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        
        subject = msg["subject"] or "(no subject)"
        sender = msg["from"] or ""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
        
        mail.logout()
        return (sender, subject, body)
    except Exception as e:
        print(f"Error fetching email: {e}")
        return None

def generate_reply(text):
    """Generate a reply using OpenAI."""
    client = OpenAI(api_key=OPENAI_API_KEY)
    messages = [
        {"role": "system", "content": "You are sir peepius aurelius of chickenopolis. You are a very noble chicken, and you are very proud."},
        {"role": "user", "content": text}
    ]
    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    return response.choices[0].message.content.strip()

def send_email(to_addr, subject, body):
    """Send an email reply."""
    msg = MIMEText(body + "\n\n— Sir Peepius Aurelius of Chickenopolis 🦊⚓")
    msg["Subject"] = f"Re: {subject}"
    msg["From"] = EMAIL_USER
    msg["To"] = to_addr
    
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
    print(f"📨 Replied to {to_addr}!")

def should_reply_to_sender(sender):
    """Check if we should reply to this sender based on TARGET_EMAILS."""
    parsed_sender = parseaddr(sender)[1] or sender
    matches_target = any(
        (t.lower() == parsed_sender.lower()) or (t.lower() in sender.lower())
        for t in TARGET_EMAILS
    )
    return matches_target, parsed_sender

def handle_gmail_notification(cloud_event=None):
    """
    Cloud Function triggered by Gmail push notifications via Pub/Sub.
    
    This function is called whenever a new email arrives in the Gmail inbox.
    It validates whether the email is from a target sender and replies if so.
    """
    try:
        # Decode the Pub/Sub message
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode()
        notification = json.loads(pubsub_message)
        
        print(f"Received Gmail notification: {notification}")
        
        # Extract the message ID (historyId is sent, but we need to fetch the actual email)
        # Note: Gmail push notifications contain historyId, not individual message IDs
        # We'll need to check recent unread messages instead
        
        # Fetch recent unread emails (since Gmail notifications don't include message content)
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        # Get the most recent unread message
        _, data = mail.search(None, "UNSEEN")
        
        if not data[0]:
            print("No unread messages found")
            mail.logout()
            return "No unread messages", 200
        
        # Process only the most recent unread message
        message_nums = data[0].split()
        latest_num = message_nums[-1]
        
        _, msg_data = mail.fetch(latest_num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        
        subject = msg["subject"] or "(no subject)"
        sender = msg["from"] or ""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
        
        mail.logout()
        
        # Check if we should reply to this sender
        should_reply, parsed_sender = should_reply_to_sender(sender)
        
        if should_reply:
            print(f"📜 From {sender}: {subject}")
            reply = generate_reply(body)
            send_email(parsed_sender, subject, reply)
            return f"Replied to {parsed_sender}", 200
        else:
            print(f"🦢 Ignoring {sender} — not one of the targets.")
            return f"Ignored {sender}", 200
            
    except Exception as e:
        print(f"Error processing notification: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

def main_local():
    """Run in local polling mode for testing."""
    print("✅ All secrets loaded. Sir Peepius is ready to sail!")
    print(f"🦊 Sir Peepius standin' by, replyin' only to {', '.join(TARGET_EMAILS)}\n")
    print("📡 Running in LOCAL MODE (polling every 15 seconds)")
    print("💡 Press Ctrl+C to stop\n")
    
    while True:
        try:
            # Simulate a notification event by checking for unread emails
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_USER, EMAIL_PASS)
            mail.select("inbox")
            
            _, data = mail.search(None, "UNSEEN")
            
            if not data[0]:
                print("🌊 No new messages…")
                mail.logout()
            else:
                # Process unread messages
                message_nums = data[0].split()
                
                for num in message_nums:
                    _, msg_data = mail.fetch(num, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    subject = msg["subject"] or "(no subject)"
                    sender = msg["from"] or ""
                    body = ""
                    
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body += part.get_payload(decode=True).decode(errors="ignore")
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")
                    
                    # Check if we should reply to this sender
                    should_reply, parsed_sender = should_reply_to_sender(sender)
                    
                    if should_reply:
                        print(f"📜 From {sender}: {subject}")
                        reply = generate_reply(body)
                        send_email(parsed_sender, subject, reply)
                    else:
                        print(f"🦢 Ignoring {sender} — not one of the targets.")
                
                mail.logout()
            
            time.sleep(15)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Sir Peepius signing off. Fair winds!")
            sys.exit(0)
        except Exception as e:
            print(f"⚠️ Error in main loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(15)

def process_latest_email():
    """Process the most recent unread email."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        _, data = mail.search(None, "UNSEEN")
        
        if not data[0]:
            print("No unread messages found")
            mail.logout()
            return "No unread messages", 200
        
        # Process the most recent unread message
        message_nums = data[0].split()
        latest_num = message_nums[-1]
        
        _, msg_data = mail.fetch(latest_num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        
        subject = msg["subject"] or "(no subject)"
        sender = msg["from"] or ""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
        
        mail.logout()
        
        # Check if we should reply to this sender
        should_reply, parsed_sender = should_reply_to_sender(sender)
        
        if should_reply:
            print(f"📜 From {sender}: {subject}")
            reply = generate_reply(body)
            send_email(parsed_sender, subject, reply)
            return f"Replied to {parsed_sender}", 200
        else:
            print(f"🦢 Ignoring {sender} — not one of the targets.")
            return f"Ignored {sender}", 200
            
    except Exception as e:
        print(f"Error processing email: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

# Flask app for local webhook server
app = Flask(__name__)

@app.route('/gmail-webhook', methods=['POST'])
def webhook():
    """Handle Gmail push notifications locally."""
    try:
        # Get the Pub/Sub message
        envelope = request.get_json()
        
        if not envelope:
            print("❌ No Pub/Sub message received")
            return "Bad Request: no Pub/Sub message", 400
        
        # Decode the message
        if 'message' in envelope:
            pubsub_message = envelope['message']
            if 'data' in pubsub_message:
                data = base64.b64decode(pubsub_message['data']).decode()
                notification = json.loads(data)
                print(f"📨 Received Gmail notification: {notification}")
        
        # Process the latest email
        result, status = process_latest_email()
        return result, status
        
    except Exception as e:
        print(f"Error in webhook: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/gmail-webhook', methods=['GET'])
def webhook_verify():
    """Handle webhook verification."""
    return "Webhook is active", 200

@app.route('/', methods=['GET'])
def health():
    """Health check endpoint."""
    return f"Sir Peepius is ready! Monitoring: {', '.join(TARGET_EMAILS)}", 200

if __name__ == "__main__":
    print("✅ All secrets loaded. Sir Peepius is ready to sail!")
    print(f"🦊 Sir Peepius standin' by, replyin' only to {', '.join(TARGET_EMAILS)}\n")
    
    # Check if we should run in webhook mode or polling mode
    mode = os.getenv("MODE", "webhook").lower()
    
    if mode == "webhook":
        print("📡 Running in WEBHOOK MODE (push notifications)")
        print("🌐 Starting local server on http://localhost:8080")
        print("💡 Make sure to:\n")
        print("   1. Expose this endpoint with ngrok: ngrok http 8080")
        print("   2. Configure Gmail watch to push to your ngrok URL")
        print("   3. Press Ctrl+C to stop\n")
        app.run(host='0.0.0.0', port=8080, debug=False)
    else:
        print("📡 Running in POLLING MODE (checking every 15 seconds)")
        print("💡 Press Ctrl+C to stop\n")
        main_local()
