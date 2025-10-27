# Sir Peepius - Local Webhook Setup Guide

## Running with Push Notifications Locally

To receive Gmail push notifications on your local machine, you need to expose your local server to the internet so Gmail can reach it.

### Step 1: Install Dependencies

```bash
pip3 install -r requirements.txt
```

### Step 2: Install ngrok (for exposing localhost)

```bash
# On macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

### Step 3: Start the Bot in Webhook Mode

```bash
python3 main.py
```

This starts a Flask server on `http://localhost:8080`

### Step 4: Expose Your Local Server with ngrok

In a **new terminal window**:

```bash
ngrok http 8080
```

You'll see output like:
```
Forwarding   https://abc123.ngrok.io -> http://localhost:8080
```

Copy that `https://abc123.ngrok.io` URL - this is your public webhook URL.

### Step 5: Configure Gmail to Push to Your Webhook

You need to set up Gmail push notifications to send to:
```
https://abc123.ngrok.io/gmail-webhook
```

**Two options:**

#### Option A: Use Google Cloud Pub/Sub (More complex but proper)

1. Create a Pub/Sub push subscription:
```bash
gcloud pubsub subscriptions create local-gmail-sub \
  --topic=gmail-notifications \
  --push-endpoint=https://abc123.ngrok.io/gmail-webhook
```

2. Set up Gmail watch (see setup_gmail_watch.py)

#### Option B: Simple polling mode (Easier for testing)

If webhook setup is too complex, just run in polling mode:

```bash
MODE=polling python3 main.py
```

This will check Gmail every 15 seconds (no ngrok needed).

## Running Modes

### Webhook Mode (default):
```bash
python3 main.py
```
- Waits for Gmail notifications via webhook
- Requires ngrok or similar tunnel
- Most efficient

### Polling Mode:
```bash
MODE=polling python3 main.py
```
- Checks Gmail every 15 seconds
- No external setup needed
- Works immediately

## Testing the Webhook

Once ngrok is running, test the webhook:

```bash
curl http://localhost:8080
```

You should see: "Sir Peepius is ready! Monitoring: your@email.com"

## Important Notes

- **ngrok URLs change** every time you restart ngrok (unless you have a paid plan)
- You'll need to **update the Pub/Sub subscription** with the new URL each time
- For production, deploy to Google Cloud Functions instead

## Troubleshooting

**"Connection refused"**
- Make sure `python3 main.py` is running
- Check the port is 8080

**"Webhook not receiving notifications"**
- Verify ngrok URL is correct
- Check Gmail watch is active
- Make sure Pub/Sub subscription points to your ngrok URL

**Want to switch modes?**
- Webhook: `python3 main.py`
- Polling: `MODE=polling python3 main.py`
