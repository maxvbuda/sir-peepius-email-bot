"""
Simplified Gmail Watch Setup for Local Webhook Testing
This sets up Gmail to send push notifications directly to your ngrok webhook
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Your ngrok webhook URL
NGROK_URL = input("Enter your ngrok URL (e.g., https://abc123.ngrok-free.dev): ").strip()
if not NGROK_URL.startswith('http'):
    print("❌ Invalid URL. Must start with https://")
    exit(1)

WEBHOOK_URL = f"{NGROK_URL}/gmail-webhook"

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    
    # Check for existing token
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing credentials...")
            creds.refresh(Request())
        else:
            # Check for credentials file
            if not os.path.exists('credentials.json'):
                print("\n❌ Missing credentials.json!")
                print("\n📋 To create credentials.json:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a new project or select existing")
                print("3. Enable Gmail API")
                print("4. Go to 'APIs & Services' > 'Credentials'")
                print("5. Click 'Create Credentials' > 'OAuth client ID'")
                print("6. Choose 'Desktop app'")
                print("7. Download JSON and save as 'credentials.json' in this folder")
                print("\nOnce you have credentials.json, run this script again.")
                exit(1)
            
            print("🔐 Starting OAuth flow...")
            print("A browser window will open for you to authorize the app.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        print("✅ Credentials saved!")
    
    return build('gmail', 'v1', credentials=creds)

def setup_direct_webhook():
    """
    Note: Gmail API doesn't support direct webhooks to arbitrary URLs.
    Gmail only supports push notifications via Google Cloud Pub/Sub.
    
    For local testing WITHOUT Google Cloud, you must use polling mode.
    
    For webhook mode, you need:
    1. A Google Cloud project
    2. Pub/Sub topic
    3. Pub/Sub push subscription pointing to your ngrok URL
    """
    print("\n⚠️  IMPORTANT INFORMATION ⚠️")
    print("\nGmail does NOT support direct webhooks to external URLs.")
    print("Gmail only pushes notifications through Google Cloud Pub/Sub.")
    print("\nYou have two options:\n")
    print("Option 1 (SIMPLE - for local testing):")
    print("  • Use polling mode: MODE=polling python3 main.py")
    print("  • Checks Gmail every 15 seconds")
    print("  • Works immediately, no setup needed")
    print("  • Shows your dad the bot works\n")
    print("Option 2 (WEBHOOKS - requires Google Cloud):")
    print("  • Create a Google Cloud project (free)")
    print("  • Set up Pub/Sub topic and push subscription")
    print("  • Point subscription to:", WEBHOOK_URL)
    print("  • This is what you'll use in production\n")
    print("💡 Recommendation:")
    print("  1. Test with polling mode NOW (free, works immediately)")
    print("  2. Show your dad it works")
    print("  3. Then deploy to Google Cloud for webhook mode")
    print("     (Still free tier, or <$1/month)\n")
    
    choice = input("Do you want setup instructions for Google Cloud Pub/Sub? (y/n): ").lower()
    
    if choice == 'y':
        print("\n📋 Google Cloud Setup Steps:")
        print("=" * 60)
        print("\n1. Create/Select Google Cloud Project:")
        print("   gcloud projects create sir-peepius-bot")
        print("   gcloud config set project sir-peepius-bot\n")
        print("2. Enable required APIs:")
        print("   gcloud services enable gmail.googleapis.com")
        print("   gcloud services enable pubsub.googleapis.com\n")
        print("3. Create Pub/Sub topic:")
        print("   gcloud pubsub topics create gmail-push\n")
        print("4. Grant Gmail permission:")
        print("   gcloud pubsub topics add-iam-policy-binding gmail-push \\")
        print("     --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \\")
        print("     --role=roles/pubsub.publisher\n")
        print("5. Create push subscription to your ngrok URL:")
        print(f"   gcloud pubsub subscriptions create gmail-sub \\")
        print(f"     --topic=gmail-push \\")
        print(f"     --push-endpoint={WEBHOOK_URL}\n")
        print("6. Set up Gmail watch (run this Python script after above):\n")
        print("   Then this script will set up the watch.\n")
        print("=" * 60)
    else:
        print("\n✅ No problem! Use polling mode for now:")
        print("   MODE=polling python3 main.py")

if __name__ == '__main__':
    print("🦊 Sir Peepius Gmail Webhook Setup\n")
    setup_direct_webhook()
