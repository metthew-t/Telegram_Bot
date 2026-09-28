#!/usr/bin/env python3
"""
Test Telegram notification directly
Usage: python backend/test_telegram_notification.py
"""

import os
import sys
import django
import requests
from dotenv import load_dotenv

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

load_dotenv()

from counselling.models import User

def test_telegram_api():
    """Test if Telegram Bot Token is valid"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    print("=" * 70)
    print("TELEGRAM BOT DIAGNOSTIC TEST")
    print("=" * 70)
    
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set in environment!")
        return False
    
    print(f"✅ Bot Token found: {token[:10]}...{token[-6:]}")
    
    # Test bot token validity
    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                print(f"✅ Bot is valid: @{bot_info['result']['username']}")
                print(f"   Bot Name: {bot_info['result']['first_name']}")
                print(f"   Bot ID: {bot_info['result']['id']}")
                return True
            else:
                print(f"❌ Bot API returned error: {bot_info}")
                return False
        else:
            print(f"❌ Bot token is INVALID (status: {response.status_code})")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to Telegram API: {e}")
        return False


def check_users_telegram_ids():
    """Check which users have telegram_id set"""
    print("\n" + "=" * 70)
    print("USER TELEGRAM IDs")
    print("=" * 70)
    
    users = User.objects.all()
    if not users.exists():
        print("⚠️ No users found in database")
        return
    
    for user in users:
        telegram_status = "✅" if user.telegram_id else "❌"
        print(f"{telegram_status} {user.username:<20} | Role: {user.role:<10} | Telegram ID: {user.telegram_id or 'NOT SET'}")


def test_send_notification():
    """Test sending a notification to a user"""
    print("\n" + "=" * 70)
    print("TEST NOTIFICATION")
    print("=" * 70)
    
    # Find a user with telegram_id
    users_with_telegram = User.objects.exclude(telegram_id__isnull=True).exclude(telegram_id='')
    
    if not users_with_telegram.exists():
        print("❌ No users have telegram_id set!")
        print("   Users need to send /start to the bot on Telegram first")
        return
    
    user = users_with_telegram.first()
    print(f"📤 Testing notification to: {user.username} (telegram_id: {user.telegram_id})")
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": str(user.telegram_id),
        "text": "🧪 *Test Notification*\n\nThis is a test message from your counselling platform. If you see this, notifications are working! ✅",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"   API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("   ✅ Test message sent successfully!")
                print(f"   Message ID: {result['result']['message_id']}")
                return True
            else:
                print(f"   ❌ API Error: {result}")
                return False
        else:
            print(f"   ❌ Failed: {response.text}")
            
            # Parse common errors
            if response.status_code == 400:
                error = response.json()
                if 'chat not found' in str(error).lower():
                    print("\n   ⚠️ ERROR EXPLANATION:")
                    print("   The user hasn't started the bot on Telegram yet!")
                    print("   They need to:")
                    print("   1. Open Telegram")
                    print("   2. Search for your bot")
                    print("   3. Send /start")
            elif response.status_code == 401:
                print("\n   ⚠️ ERROR EXPLANATION:")
                print("   Bot token is INVALID or REVOKED!")
                print("   Check your TELEGRAM_BOT_TOKEN environment variable")
            
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def main():
    # Step 1: Test bot token
    bot_valid = test_telegram_api()
    
    # Step 2: Check users
    check_users_telegram_ids()
    
    # Step 3: Test notification (only if bot is valid)
    if bot_valid:
        test_send_notification()
    
    print("\n" + "=" * 70)
    print("SUMMARY & NEXT STEPS")
    print("=" * 70)
    
    if not bot_valid:
        print("❌ Bot token is invalid!")
        print("   → Check TELEGRAM_BOT_TOKEN in Render environment variables")
        print("   → Get a new token from @BotFather if needed")
    else:
        users_with_telegram = User.objects.exclude(telegram_id__isnull=True).exclude(telegram_id='')
        if not users_with_telegram.exists():
            print("⚠️ No users have telegram_id!")
            print("   → Users need to send /start to bot on Telegram")
            print("   → Make sure bot is running on Render")
        else:
            print("✅ Bot token is valid")
            print("✅ Users have telegram_id set")
            print("   → If notifications still not working:")
            print("     1. Check bot is running on Render (look for '🤖 TELEGRAM BOT STARTING' in logs)")
            print("     2. Check user has started the bot (send /start)")
            print("     3. Check Render logs for notification attempts")


if __name__ == '__main__':
    main()
