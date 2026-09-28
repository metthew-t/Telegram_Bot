#!/usr/bin/env python3
"""
Simple notification test - Run this on Render Shell
Usage: python backend/test_notification_simple.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User, Case
from counselling.views import send_telegram_notification

print("=" * 80)
print("🧪 TELEGRAM NOTIFICATION TEST")
print("=" * 80)
print()

# Check environment
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
backend_url = os.getenv('BACKEND_URL')

print("📋 ENVIRONMENT VARIABLES:")
print(f"   Bot Token: {bot_token[:20]}...{bot_token[-6:] if bot_token else '❌ MISSING'}")
print(f"   Backend URL: {backend_url or '❌ MISSING'}")
print()

# Check users
users = User.objects.filter(role='user')
print(f"👥 USERS IN DATABASE: {users.count()}")
print()

users_with_telegram = users.exclude(telegram_id__isnull=True).exclude(telegram_id='')
users_without_telegram = users.filter(telegram_id__isnull=True) | users.filter(telegram_id='')

print(f"✅ Users WITH telegram_id: {users_with_telegram.count()}")
print(f"❌ Users WITHOUT telegram_id: {users_without_telegram.count()}")
print()

if users_without_telegram.exists():
    print("⚠️ USERS NEED TO /START BOT:")
    for u in users_without_telegram:
        print(f"   - {u.username}")
    print()

# Test notification for each user with telegram_id
if users_with_telegram.exists():
    print("🧪 TESTING NOTIFICATIONS:")
    print("-" * 80)
    
    for user in users_with_telegram:
        print(f"\n📱 Testing for: {user.username}")
        print(f"   Telegram ID: {user.telegram_id}")
        
        # Get user's latest case
        cases = Case.objects.filter(user=user).order_by('-id')
        if cases.exists():
            case = cases.first()
            case_num = case.user_case_number if case.user_case_number else case.id
            print(f"   Latest case: #{case_num}")
        
        # Send test notification
        test_message = f"🧪 Test notification from Render\n\nIf you see this, notifications are working! ✅"
        
        print(f"   Sending test message...")
        success = send_telegram_notification(user.telegram_id, test_message)
        
        if success:
            print(f"   ✅ SUCCESS! Check Telegram!")
        else:
            print(f"   ❌ FAILED! Check logs above for error.")
        print()
else:
    print("⚠️ NO USERS WITH TELEGRAM ID!")
    print("   Users must send /start to bot first.")
    print()

print("=" * 80)
print("✅ TEST COMPLETE!")
print("=" * 80)
print()
print("💡 NEXT STEPS:")
print("   1. If test succeeded: Notifications are working!")
print("   2. If test failed: Check error messages above")
print("   3. If no users have telegram_id: Users need to /start bot")
print()
