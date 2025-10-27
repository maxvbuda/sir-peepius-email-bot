# Sir Peepius Email Bot - Google Cloud Setup Guide

This guide will help you deploy Sir Peepius as a serverless Google Cloud Function that responds to emails instantly using Gmail push notifications instead of polling.

## Cost Comparison

**Old polling method (every 15 seconds):**
- ~175,200 checks per month
- Constant Cloud Compute/VM costs

**New push notification method:**
- Only runs when email arrives
- Pay only for actual executions
- Typically < $1/month for normal email volume

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Gmail Account** with App Password enabled
3. **OpenAI API Key**
4. **gcloud CLI** installed ([Install Guide](https://cloud.google.com/sdk/docs/install))

## Step 1: Set Up Google Cloud Project

```bash
# Create a new project or use existing
gcloud projects create sir-peepius-bot --name="Sir Peepius Bot"

# Set as active project
gcloud config set project sir-peepius-bot

# Enable required APIs
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable gmail.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Step 2: Create Pub/Sub Topic

```bash
# Create the topic that Gmail will publish to
gcloud pubsub topics create gmail-notifications

# Grant Gmail permission to publish to this topic
gcloud pubsub topics add-iam-policy-binding gmail-notifications \
  --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
  --role=roles/pubsub.publisher
```

## Step 3: Set Up Gmail Push Notifications

### Option A: Using OAuth2 (Recommended for production)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to "APIs & Services" > "Credentials"
3. Create OAuth 2.0 credentials
4. Use the Gmail API to set up watch on your mailbox

### Option B: Using App Password (Simpler for personal use)

1. Go to your Google Account settings
2. Security > 2-Step Verification
3. App passwords > Generate new app password
4. Save this password for the deployment

Then run this Python script to set up the watch:

```python
# setup_gmail_watch.py
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# You'll need to set up OAuth2 credentials first
# Follow: https://developers.google.com/gmail/api/quickstart/python

PROJECT_ID = "sir-peepius-bot"
TOPIC_NAME = "gmail-notifications"

service = build('gmail', 'v1', credentials=creds)

request = {
    'topicName': f'projects/{PROJECT_ID}/topics/{TOPIC_NAME}',
    'labelIds': ['INBOX']
}

service.users().watch(userId='me', body=request).execute()
print("✅ Gmail watch set up successfully!")
```

## Step 4: Configure Environment Variables

Edit `deploy.sh` and update these values:

```bash
PROJECT_ID="sir-peepius-bot"  # Your GCP project ID
EMAIL_USER="your-email@gmail.com"  # Your Gmail address
EMAIL_PASS="your-app-password"  # Gmail app password
OPENAI_API_KEY="sk-..."  # Your OpenAI API key
TARGET_EMAILS="friend@example.com,colleague@example.com"  # Who to reply to
```

## Step 5: Deploy to Google Cloud

```bash
# Make deploy script executable
chmod +x deploy.sh

# Deploy the function
./deploy.sh
```

Or deploy manually:

```bash
gcloud functions deploy sir-peepius-email-bot \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=handle_gmail_notification \
  --trigger-topic=gmail-notifications \
  --set-env-vars="EMAIL_USER=your-email@gmail.com,EMAIL_PASS=your-app-password,OPENAI_API_KEY=sk-...,TARGET_EMAILS=email1@example.com" \
  --max-instances=10 \
  --memory=256MB \
  --timeout=60s
```

## Step 6: Test the Function

Send a test email to your Gmail from one of the TARGET_EMAILS addresses and check:

```bash
# View logs
gcloud functions logs read sir-peepius-email-bot --region=us-central1 --limit=50
```

## Important Notes

### Gmail Watch Expiration
Gmail watch requests expire after 7 days. You need to renew them. Options:

1. **Manual renewal**: Run the watch setup script weekly
2. **Automated renewal**: Set up a Cloud Scheduler job to renew automatically:

```bash
# Create a Cloud Scheduler job to renew the watch every 6 days
gcloud scheduler jobs create http renew-gmail-watch \
  --schedule="0 0 */6 * *" \
  --uri="https://your-renewal-function-url" \
  --http-method=POST
```

### Security Best Practices

1. **Never commit credentials** to git
2. Use **Secret Manager** instead of environment variables for production:
   ```bash
   # Store secrets in Secret Manager
   echo -n "your-app-password" | gcloud secrets create gmail-app-password --data-file=-
   ```
3. Enable **VPC Service Controls** for additional security
4. Set up **alerts** for unusual function invocations

### Cost Optimization

- Set `--max-instances=10` to limit concurrent executions
- Use `--memory=256MB` (minimum needed)
- Set `--timeout=60s` (emails should process quickly)

### Monitoring

View metrics in Cloud Console:
- Functions > sir-peepius-email-bot > Metrics
- Monitor invocations, errors, and execution time

## Troubleshooting

### Function not triggering
- Check Gmail watch is active: `gcloud pubsub subscriptions list`
- Verify topic permissions: `gcloud pubsub topics get-iam-policy gmail-notifications`
- Check function logs for errors

### Authentication errors
- Verify Gmail App Password is correct
- Check that 2FA is enabled on Gmail account
- Ensure OPENAI_API_KEY is valid

### Function timing out
- Increase timeout: `--timeout=120s`
- Check if OpenAI API is responding slowly
- Review logs for bottlenecks

## Files Created

- `main.py` - Cloud Function handler (replaces the polling version)
- `requirements.txt` - Python dependencies
- `deploy.sh` - Deployment script
- `SETUP.md` - This setup guide

## Migration from Polling Version

The old `fox_email_bot_better.py` is no longer needed for Cloud deployment. It used a polling loop that checked every 15 seconds. The new `main.py`:

- ✅ Runs only when email arrives (push notifications)
- ✅ Much lower cost
- ✅ Faster response time
- ✅ No idle resource consumption

You can keep the old version for local testing if needed.
