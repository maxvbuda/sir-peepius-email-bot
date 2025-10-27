#!/bin/bash

# Deploy Sir Peepius Email Bot to Google Cloud Functions
# Make sure you've set up Gmail push notifications first (see SETUP.md)

# Configuration
PROJECT_ID="your-project-id"  # Replace with your GCP project ID
FUNCTION_NAME="sir-peepius-email-bot"
REGION="us-central1"  # Choose your preferred region
TOPIC_NAME="gmail-notifications"  # The Pub/Sub topic Gmail pushes to

# Set environment variables for the function
# IMPORTANT: Replace these with your actual credentials
EMAIL_USER="your-email@gmail.com"
EMAIL_PASS="your-app-password"
OPENAI_API_KEY="your-openai-api-key"
TARGET_EMAILS="email1@example.com,email2@example.com"

echo "🚀 Deploying Sir Peepius to Google Cloud Functions..."

gcloud functions deploy $FUNCTION_NAME \
  --gen2 \
  --runtime=python311 \
  --region=$REGION \
  --source=. \
  --entry-point=handle_gmail_notification \
  --trigger-topic=$TOPIC_NAME \
  --set-env-vars="EMAIL_USER=$EMAIL_USER,EMAIL_PASS=$EMAIL_PASS,OPENAI_API_KEY=$OPENAI_API_KEY,TARGET_EMAILS=$TARGET_EMAILS" \
  --max-instances=10 \
  --memory=256MB \
  --timeout=60s

echo "✅ Deployment complete!"
echo "📝 Make sure Gmail push notifications are configured to publish to topic: $TOPIC_NAME"
