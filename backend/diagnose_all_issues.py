#!/usr/bin/env python3
"""
Complete diagnostic for both issues:
1. Owner login
2. Telegram notifications

Run on Render Shell: python backend/diagnose_all_issues.py
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User, Case, Message
from django.contrib.auth import authenticate
from counselling.views import send_telegram_notification
import requests

print("=" * 80)
print("🔍 COMPLETE DIAGNOSTIC - Owner Login & Telegram Notifications")
print("=" * 80)
print()

# ═══════════════════════════════════════════════════════════════════════════
# ISSUE 1: Owner Login
# ═══════════════════════════════════════════════════════════════════════════
print("📋 ISSUE 1: OWNER LOGIN")
print("-" * 80)

# Check if owner exists
owner = User.objects.filter(username='owner').first()

if not owner:
    print("❌ NO OWNER ACCOUNT EXISTS!")
    print("   Creating owner now...")
    owner = User(username='owner', email='owner@example.com', role='owner')
    owner.set_password('owner1234')
    owner.email_verified = True
    owner.save()
    print("✅ Created owner account")
    print(f"   Username: owner")
    print(f"   Password: owner1234")
else:
    print(f"✅ Owner account exists:")
    print(f"   Username: {owner.username}")
    print(f"   Email: {owner.email}")
    print(f"   Role: {owner.role}")
    print(f"   Email verified: {owner.email_verified}")
    print(f"   Is active: {owner.is_active}")

# Test authentication
print("\n🔐 Testing authentication...")
test_user = authenticate(username='owner', password='owner1234')

if test_user:
    print("✅ Authentication SUCCESSFUL!")
    print(f"   Authenticated as: {test_user.username}")
    print(f"   Role: {test_user.role}")
else:
    print("❌ Authentication FAILED!")
    print("   Resetting password...")
    owner.set_password('owner1234')
    owner.email_verified = True
    owner.save()
    print("✅ Password reset to: owner1234")
    
    # Test again
    test_user = authenticate(username='owner', password='owner1234')
    if test_user:
        print("✅ Authentication now works!")
    else:
        print("❌ Still failing - database issue!")

print()

# ═══════════════════════════════════════════════════════════════════════════
# ISSUE 2: Telegram Notifications
# ═══════════════════════════════════════════════════════════════════════════
print("📋 ISSUE 2: TELEGRAM NOTIFICATIONS")
print("-" * 80)

# Check environment variables
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
backend_url = os.getenv('BACKEND_URL')

print(f"Bot Token: {bot_token[:20]}...{bot_token[-6:] if bot_token else '❌ MISSING'}")
print(f"Backend URL: {backend_url or '❌ MISSING'}")
print()

# Check users with telegram_id
users_with_telegram = User.objects.filter(role='user').exclude(telegram_id__isnull=True).exclude(telegram_id='')
users_without_telegram = User.objects.filter(role='user').filter(telegram_id__isnull=True) | User.objects.filter(role='user').filter(telegram_id='')

print(f"👥 USERS:")
print(f"   Total users: {User.objects.filter(role='user').count()}")
print(f"   ✅ With telegram_id: {users_with_telegram.count()}")
print(f"   ❌ Without telegram_id: {users_without_telegram.count()}")
print()

if users_without_telegram.exists():
    print("⚠️ USERS WITHOUT TELEGRAM_ID (need to /start bot):")
    for u in users_without_telegram:
        print(f"   - {u.username}")
    print()

# Check cases
cases = Case.objects.all().order_by('-id')[:5]
print(f"📋 RECENT CASES: {cases.count()}")
for case in cases:
    print(f"\n   Case #{case.id} (User Case #{case.user_case_number or 'N/A'})")
    print(f"   User: {case.user.username}")
    print(f"   User telegram_id: {case.user.telegram_id or '❌ NONE'}")
    print(f"   Status: {case.status}")
    print(f"   Can receive notifications: {'✅ YES' if case.user.telegram_id else '❌ NO'}")
    
    # Get latest messages
    messages = Message.objects.filter(case=case).order_by('-id')[:3]
    if messages:
        print(f"   Recent messages:")
        for msg in messages:
            sender_role = msg.sender.role if msg.sender else 'unknown'
            print(f"     - {sender_role}: {msg.content[:50]}...")

print()
print("-" * 80)

# Test notification for users with telegram_id
if users_with_telegram.exists():
    print("\n🧪 TESTING TELEGRAM NOTIFICATIONS:")
    print("-" * 80)
    
    for user in users_with_telegram[:3]:  # Test first 3 users
        print(f"\n📱 Testing for: {user.username}")
        print(f"   Telegram ID: {user.telegram_id}")
        
        # Send test notification
        test_message = f"🧪 Test from Render Shell\n\nIf you see this, notifications work! ✅"
        
        print(f"   Sending test notification...")
        success = send_telegram_notification(user.telegram_id, test_message)
        
        if success:
            print(f"   ✅ SUCCESS! User should receive message on Telegram!")
        else:
            print(f"   ❌ FAILED! Check errors above.")
        
        # Also test with bot API directly
        if bot_token:
            print(f"   Testing direct Telegram API call...")
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": user.telegram_id,
                "text": "🧪 Direct API test from diagnostic script"
            }
            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    print(f"   ✅ Direct API call SUCCESS!")
                else:
                    print(f"   ❌ Direct API call FAILED: {response.status_code}")
                    print(f"   Error: {response.text}")
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
else:
    print("\n⚠️ NO USERS WITH TELEGRAM_ID - Cannot test notifications")
    print("   Users must send /start to bot first!")

print()
print("=" * 80)
print("📊 SUMMARY")
print("=" * 80)

# Issue 1 Summary
print("\n1️⃣ OWNER LOGIN:")
if authenticate(username='owner', password='owner1234'):
    print("   ✅ WORKING - Credentials: owner / owner1234")
else:
    print("   ❌ NOT WORKING - Need to reset password")

# Issue 2 Summary
print("\n2️⃣ TELEGRAM NOTIFICATIONS:")
if not bot_token:
    print("   ❌ Bot token not set in environment!")
elif users_with_telegram.count() == 0:
    print("   ⚠️ No users have telegram_id - users need to /start bot")
else:
    print(f"   ✅ {users_with_telegram.count()} user(s) can receive notifications")
    print("   Run test above to verify notifications work")

print()
print("=" * 80)
print("✅ DIAGNOSTIC COMPLETE!")
print("=" * 80)
print()

# Recommendations
print("💡 RECOMMENDATIONS:")
print()

if not authenticate(username='owner', password='owner1234'):
    print("1. FIX OWNER LOGIN:")
    print("   Run: python backend/update_owner.py")
    print()

if users_without_telegram.exists():
    print("2. FIX TELEGRAM NOTIFICATIONS:")
    print("   Tell users to send /start to bot on Telegram")
    print(f"   Affected users: {', '.join([u.username for u in users_without_telegram])}")
    print()

if bot_token and users_with_telegram.exists():
    print("3. TEST NOTIFICATIONS:")
    print("   Have admin reply to a case")
    print("   Check if user receives notification on Telegram")
    print("   Check Render logs for [TELEGRAM NOTIFICATION] lines")
    print()

print("=" * 80)
