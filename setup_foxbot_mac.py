#!/usr/bin/env python3
import os, sys
from dotenv import load_dotenv, find_dotenv
env_path = find_dotenv()
if not env_path:
    print("❌ No .env found in this folder."); sys.exit(1)
print("✅ Found .env:", env_path)
load_dotenv(env_path)
ok = lambda v: "✅" if v else "❌"
api = os.getenv("OPENAI_API_KEY")
user= os.getenv("EMAIL_USER")
pw  = os.getenv("EMAIL_PASS")
print("OPENAI_API_KEY:", ok(api))
print("EMAIL_USER:", user if user else "❌ None")
print("EMAIL_PASS:", ok(pw))
if all([api,user,pw]):
    print("\n🦊 All set. Run:  python3 fox_email_bot_better.py")
else:
    print("\n⚠️ Missing values. Edit .env and run again.")
