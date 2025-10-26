import imaplib, smtplib, email, os, time, json, sys
from email.mime.text import MIMEText
from dotenv import load_dotenv
from openai import OpenAI

# 🧭 Load secrets safely
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path)

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🦊 Choose yer noble correspondent
TARGET_EMAIL = "friend@example.com"  # ← change to the one person ye reply to

# ⚓ Sanity check before sailing
missing = [k for k, v in {
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "EMAIL_USER": EMAIL_USER,
    "EMAIL_PASS": EMAIL_PASS,
}.items() if not v]

if missing:
    print("❌ Missing the following secrets in .env:", ", ".join(missing))
    print("Fix yer .env file before setting sail!")
    sys.exit(1)
else:
    print("✅ All secrets loaded! Sir Peepius ready to sail.\n")

# 🗝️ Setup constants
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
MEMORY_FILE = "fox_memory.json"

# 📜 Load/save conversation memory
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory[-10:], f, indent=2)

# 🦜 Fetch unread messages
def fetch_unread_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        status, messages = mail.search(None, "UNSEEN")
        emails = []
        for num in messages[0].split():
            _, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            subject = msg["subject"] or "(no subject)"
            sender = msg["from"] or ""
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
    except Exception as e:
        print("⚠️ Error fetchin’ emails:", e)
        return []

# 🤖 Summon GPT-5 for witty replies
def generate_reply(message_text, memory):
    client = OpenAI(api_key=OPENAI_API_KEY)
    conversation = [
        {"role": "system", "content": (
            "Ye be Sir Peepius Aurelius of Chickenopolis, a noble, clever pirate-fox "
            "who remembers past voyages and replies to emails with grace and wit."
        )}
    ] + memory + [{"role": "user", "content": message_text}]
    try:
        completion = client.chat.completions.create(model="gpt-5", messages=conversation)
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("⚠️ Trouble summonin’ GPT:", e)
        return "(Sir Peepius be temporarily speechless, arrr.)"

# 📬 Send email reply
def send_email(to_addr, subject, body):
    msg = MIMEText(body + "\n\n— Sir Peepius Aurelius of Chickenopolis 🦊⚓")
    msg["Subject"] = f"Re: {subject}"
    msg["From"] = EMAIL_USER
    msg["To"] = to_addr
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"📨 Sent reply to {to_addr}!")
    except Exception as e:
        print("⚠️ Could not send email:", e)

# 🧭 Main loop
def main():
    print(f"🦊 Sir Peepius Aurelius standin’ by, replyin’ only to {TARGET_EMAIL}\n")
    memory = load_memory()

    while True:
        emails = fetch_unread_emails()
        if not emails:
            print("🌊 No new messages...")
        else:
            for sender, subject, body in emails:
                if TARGET_EMAIL.lower() in sender.lower():
                    print(f"📜 Message from {sender}: {subject}")
                    reply = generate_reply(body, memory)
                    send_email(TARGET_EMAIL, subject, reply)
                    memory.append({"role": "user", "content": body})
                    memory.append({"role": "assistant", "content": reply})
                    save_memory(memory)
                else:
                    print(f"🦢 Ignorin’ {sender} — not the chosen one.")
        time.sleep(60)  # check inbox every minute

if __name__ == "__main__":
    main()
