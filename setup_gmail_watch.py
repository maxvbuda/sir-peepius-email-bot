"""
Helper script to set up Gmail push notifications.
Run this after deploying the Cloud Function to enable Gmail watch.
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes needed
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.modify']

# Your GCP project details
PROJECT_ID = "sir-peepius-bot"  # Update with your project ID
TOPIC_NAME = "gmail-notifications"

def get_gmail_service():
    """Authenticate and return Gmail API service."""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # You need to create credentials.json from Google Cloud Console
            # Go to APIs & Services > Credentials > Create OAuth client ID
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def setup_watch():
    """Set up Gmail push notifications."""
    try:
        service = get_gmail_service()
        
        request = {
            'topicName': f'projects/{PROJECT_ID}/topics/{TOPIC_NAME}',
            'labelIds': ['INBOX'],
            'labelFilterAction': 'include'
        }
        
        result = service.users().watch(userId='me', body=request).execute()
        
        print("✅ Gmail watch set up successfully!")
        print(f"📧 Watching for new emails in INBOX")
        print(f"📅 Expires: {result.get('expiration')} (renew in ~7 days)")
        print(f"🔔 History ID: {result.get('historyId')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error setting up watch: {e}")
        print("\nMake sure you have:")
        print("1. Created OAuth credentials in Google Cloud Console")
        print("2. Downloaded credentials.json to this directory")
        print("3. Enabled Gmail API for your project")
        return None

def stop_watch():
    """Stop Gmail push notifications."""
    try:
        service = get_gmail_service()
        service.users().stop(userId='me').execute()
        print("✅ Gmail watch stopped")
    except Exception as e:
        print(f"❌ Error stopping watch: {e}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'stop':
        stop_watch()
    else:
        print("🦊 Setting up Gmail push notifications for Sir Peepius...")
        print(f"📡 Topic: projects/{PROJECT_ID}/topics/{TOPIC_NAME}\n")
        setup_watch()
        print("\n💡 Tip: Run 'python setup_gmail_watch.py stop' to disable notifications")
