"""
Simple Gmail Watch Setup Script
This sets up Gmail to push notifications to Google Cloud Pub/Sub
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/gmail.modify']

# Your Google Cloud project details  
PROJECT_ID = "peepius"  # Your project ID
TOPIC_NAME = "gmail-notifications"  # The Pub/Sub topic we created

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
                print("1. Go to https://console.cloud.google.com/apis/credentials")
                print(f"2. Make sure project 'peepius' is selected at the top")
                print("3. Click '+ CREATE CREDENTIALS' > 'OAuth client ID'")
                print("4. Application type: 'Desktop app'")
                print("5. Name: 'Sir Peepius Gmail Bot'")
                print("6. Click 'CREATE'")
                print("7. Click 'DOWNLOAD JSON'")
                print("8. Save the file as 'credentials.json' in this folder:")
                print(f"   {os.getcwd()}")
                print("\nOnce you have credentials.json, run this script again.")
                return None
            
            print("🔐 Starting OAuth flow...")
            print("A browser window will open for you to authorize the app.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        print("✅ Credentials saved!")
    
    return build('gmail', 'v1', credentials=creds)

def setup_gmail_watch():
    """Set up Gmail to push notifications to Pub/Sub."""
    print("🦊 Setting up Gmail push notifications for Sir Peepius...\n")
    
    service = get_gmail_service()
    if not service:
        return
    
    try:
        request = {
            'topicName': f'projects/{PROJECT_ID}/topics/{TOPIC_NAME}',
            'labelIds': ['INBOX'],
            'labelFilterAction': 'include'
        }
        
        result = service.users().watch(userId='me', body=request).execute()
        
        print("\n✅ Gmail watch set up successfully!")
        print(f"📧 Watching INBOX for new emails")
        print(f"📡 Publishing to: projects/{PROJECT_ID}/topics/{TOPIC_NAME}")
        print(f"⏰ Expires in ~7 days (you'll need to renew)")
        print(f"\n🎉 Your webhook is now active!")
        print(f"\nNext steps:")
        print(f"1. Make sure python3 main.py is running")
        print(f"2. Make sure ngrok is running")
        print(f"3. Send a test email from one of your target addresses")
        print(f"4. Watch Sir Peepius reply instantly!")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error setting up watch: {e}")
        print("\nTroubleshooting:")
        print("- Make sure you created OAuth credentials (not API key)")
        print("- Make sure Gmail API is enabled")
        print("- Try deleting token.pickle and running again")
        return None

if __name__ == '__main__':
    setup_gmail_watch()
