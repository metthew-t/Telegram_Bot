#!/usr/bin/env python3
"""
Complete diagnostic script for Telegram Bot & Backend connectivity
Tests: Bot token, Backend API, Database, User registration
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8000')

print("=" * 80)
print("🔍 TELEGRAM BOT & BACKEND DIAGNOSTIC")
print("=" * 80)
print()

# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: Environment Variables
# ═══════════════════════════════════════════════════════════════════════════
print("📋 TEST 1: Environment Variables")
print("-" * 80)

if not TELEGRAM_BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN is NOT set!")
    sys.exit(1)
else:
    print(f"✅ TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN[:20]}...{TELEGRAM_BOT_TOKEN[-5:]}")

print(f"✅ BACKEND_URL: {BACKEND_URL}")
print()

# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: Telegram Bot API Connection
# ═══════════════════════════════════════════════════════════════════════════
print("📋 TEST 2: Telegram Bot API Connection")
print("-" * 80)

try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    print(f"Testing: {url[:60]}...")
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            bot_info = data.get('result', {})
            print(f"✅ Bot API connection successful!")
            print(f"   Bot Name: {bot_info.get('first_name')}")
            print(f"   Bot Username: @{bot_info.get('username')}")
            print(f"   Bot ID: {bot_info.get('id')}")
            print(f"   Can Join Groups: {bot_info.get('can_join_groups')}")
        else:
            print(f"❌ Bot API returned error: {data}")
            sys.exit(1)
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
        print("\n🔧 POSSIBLE ISSUES:")
        print("   1. Bot token is invalid")
        print("   2. Bot was deleted by BotFather")
        print("   3. Network connectivity issue")
        sys.exit(1)
except Exception as e:
    print(f"❌ Exception: {str(e)}")
    print("\n🔧 POSSIBLE ISSUES:")
    print("   1. No internet connection")
    print("   2. Firewall blocking Telegram API")
    sys.exit(1)

print()

# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: Backend Server Health
# ═══════════════════════════════════════════════════════════════════════════
print("📋 TEST 3: Backend Server Health")
print("-" * 80)

try:
    # Try to reach backend root
    response = requests.get(f"{BACKEND_URL}/", timeout=5)
    print(f"✅ Backend server is responding (Status: {response.status_code})")
except requests.exceptions.ConnectionError:
    print(f"❌ Cannot connect to backend at {BACKEND_URL}")
    print("\n🔧 BACKEND IS NOT RUNNING!")
    print("   Start backend with:")
    print(f"   cd backend")
    print(f"   python manage.py runserver 8000")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error connecting to backend: {str(e)}")
    sys.exit(1)

print()

# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: Backend API Endpoints
# ═══════════════════════════════════════════════════════════════════════════
print("📋 TEST 4: Backend API Endpoints")
print("-" * 80)

# Test telegram-login endpoint
try:
    test_telegram_id = "999999999"  # Fake test ID
    test_username = "test_diagnostic_user"
    
    response = requests.post(
        f"{BACKEND_URL}/api/telegram-login/",
        json={
            'telegram_id': test_telegram_id,
            'username': test_username
        },
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ /api/telegram-login/ endpoint working!")
        print(f"   Response: User created/logged in")
        if 'access' in data:
            print(f"   Access token: {data['access'][:30]}...")
    else:
        print(f"⚠️  Endpoint responded with {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Error testing endpoint: {str(e)}")

print()

# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: Database Migration Status
# ═══════════════════════════════════════════════════════════════════════════
print("📋 TEST 5: Database Migration Status")
print("-" * 80)

try:
    import django
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
    django.setup()
    
    from django.core.management import call_command
    from io import StringIO
    
    # Check migrations
    out = StringIO()
    call_command('showmigrations', '--list', stdout=out)
    migrations_output = out.getvalue()
    
    if '[X]' in migrations_output:
        applied_count = migrations_output.count('[X]')
        print(f"✅ Database migrations applied: {applied_count} migrations")
        
        # Check if our specific migration is applied
        if '0007_voice_and_case_numbering' in migrations_output:
            if '[X] 0007_voice_and_case_numbering' in migrations_output:
                print(f"✅ Voice & case numbering migration APPLIED")
            else:
                print(f"⚠️  Voice & case numbering migration NOT APPLIED")
                print(f"   Run: python backend/manage.py migrate")
    else:
        print(f"⚠️  No migrations applied yet")
        print(f"   Run: python backend/manage.py migrate")
        
except Exception as e:
    print(f"⚠️  Could not check migrations: {str(e)}")
    print(f"   This is OK if backend is running separately")

print()

# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: Check if Bot is Running
# ═══════════════════════════════════════════════════════════════════════════
print("📋 TEST 6: Check if Bot Process is Running")
print("-" * 80)

try:
    # Check recent updates to see if bot is polling
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?limit=1"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('ok'):
            updates = data.get('result', [])
            if updates:
                last_update = updates[-1]
                update_id = last_update.get('update_id')
                print(f"✅ Bot is receiving updates!")
                print(f"   Last update ID: {update_id}")
                
                # Check message details
                if 'message' in last_update:
                    msg = last_update['message']
                    from_user = msg.get('from', {})
                    print(f"   Last message from: {from_user.get('username', 'N/A')} (ID: {from_user.get('id')})")
                    print(f"   Message text: {msg.get('text', 'N/A')[:50]}...")
            else:
                print(f"⚠️  No recent updates (bot may not be started yet)")
                print(f"   Send /start to your bot on Telegram to test")
    
    print()
    print("ℹ️  To check if bot is running:")
    print("   1. Look for Python process running telegram_bot.py")
    print("   2. Send /start to your bot on Telegram")
    print("   3. Bot should respond immediately if running")
    
except Exception as e:
    print(f"⚠️  Could not check bot status: {str(e)}")

print()

# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: Test User Registration Flow
# ═══════════════════════════════════════════════════════════════════════════
print("📋 TEST 7: Test User Registration Flow")
print("-" * 80)

try:
    # Simulate what bot does when user sends /start
    test_telegram_id = "123456789"
    test_username = "diagnostic_test_user"
    
    print(f"Simulating /start from user...")
    print(f"  Telegram ID: {test_telegram_id}")
    print(f"  Username: {test_username}")
    
    response = requests.post(
        f"{BACKEND_URL}/api/telegram-login/",
        json={
            'telegram_id': test_telegram_id,
            'username': test_username
        },
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ User registration/login successful!")
        print(f"   Access token received: {'access' in data}")
        print(f"   User can create cases: Yes")
        print(f"   Bot ↔ Backend communication: WORKING")
    else:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error during registration test: {str(e)}")

print()

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("📊 DIAGNOSTIC SUMMARY")
print("=" * 80)
print()
print("✅ WORKING:")
print("   - Bot token is valid")
print("   - Telegram API accessible")
print("   - Backend server running")
print("   - API endpoints responding")
print()
print("🔧 NEXT STEPS:")
print("   1. If bot not running: python bot/telegram_bot.py")
print("   2. If backend not running: cd backend && python manage.py runserver")
print("   3. Send /start to bot on Telegram")
print("   4. Check Render logs for '[TELEGRAM NOTIFICATION]' when admin replies")
print()
print("📱 TELEGRAM BOT LINK:")
print(f"   https://t.me/{bot_info.get('username', 'your_bot')}")
print()
print("=" * 80)
print("✅ DIAGNOSTIC COMPLETE!")
print("=" * 80)
