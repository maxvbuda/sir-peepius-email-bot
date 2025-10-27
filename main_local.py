#!/usr/bin/env python3
"""
Sir Peepius Email Bot - Local Version
Run this locally to test before deploying to Google Cloud
"""

import imaplib
import smtplib
import email
import os
import time
import sys
from email.utils import parseaddr
from email.mime.text import MIMEText
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TARGET_EMAILS_ENV = os.getenv("TARGET_EMAILS")

if not TARGET_EMAILS_ENV:
    print("❌ Missing TARGET_EMAILS in .env or environment.\nPlease set TARGET_EMAILS to a comma-separated list of addresses, e.g. TARGET_EMAILS=\"a@x.com,b@y.com\".")
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

print("✅ All secrets loaded. Sir Peepius is ready to sail!\n")

IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def fetch_unread():
    """Fetch unread emails from Gmail."""
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    _, data = mail.search(None, "UNSEEN")
    emails = []
    for num in data[0].split():
        _, msg_data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        subject = msg["subject"]
        sender = msg["from"]
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_payload(decode=True).decode(errors="ignore")
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")
        emails.append((sender, subject, body))
    mail.logout()
    return emails

def generate_reply(text):
    """Generate reply using OpenAI."""
    client = OpenAI(api_key=OPENAI_API_KEY)
    messages = [
        {"role": "system", "content": "You are sir peepius aurelius of chickenopolis. You are a very noble chicken, and you are very proud."},
        {"role": "user", "content": text}
    ]
    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    return response.choices[0].message.content.strip()

def send_email(to_addr, subject, body):
    """Send email reply."""
    msg = MIMEText(body + "\n\n— Sir Peepius Aurelius of Chickenopolis 🦊⚓")
    msg["Subject"] = f"Re: {subject}"
    msg["From"] = EMAIL_USER
    msg["To"] = to_addr
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
    print(f"📨 Replied to {to_addr}!")

def main():
    print(f"🦊 Sir Peepius standin' by, replyin' only to {', '.join(TARGET_EMAILS)}\n")
    while True:
        mails = fetch_unread()
        if not mails:
            print("🌊 No new messages…")
        else:
            for sender, subject, body in mails:
                # Parse the envelope 'From' address and check against targets.
                parsed_sender = parseaddr(sender)[1] or sender
                matches_target = any(
                    (t.lower() == parsed_sender.lower()) or (t.lower() in sender.lower())
                    for t in TARGET_EMAILS
                )
                if matches_target:
                    print(f"📜 From {sender}: {subject}")
                    reply = generate_reply(body)
                    # Reply to the actual parsed sender address (not the configured target)
                    send_email(parsed_sender, subject, reply)
                else:
                    print(f"🦢 Ignorin' {sender} — not one of the targets.")
        time.sleep(15)

if __name__ == "__main__":
    main()
