#!/usr/bin/env python3
"""
Check if users have telegram_id saved in database
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User, Case

print("=" * 80)
print("🔍 CHECKING TELEGRAM IDs IN DATABASE")
print("=" * 80)
print()

# Check all users
users = User.objects.all()
print(f"📊 Total users in database: {users.count()}")
print()

print("👥 USER DETAILS:")
print("-" * 80)
for user in users:
    telegram_status = "✅ HAS telegram_id" if user.telegram_id else "❌ NO telegram_id"
    print(f"Username: {user.username}")
    print(f"  Role: {user.role}")
    print(f"  Email: {user.email}")
    print(f"  Telegram ID: {user.telegram_id or 'None'}")
    print(f"  Status: {telegram_status}")
    print()

print("-" * 80)
print()

# Check users with telegram_id
users_with_telegram = User.objects.exclude(telegram_id__isnull=True).exclude(telegram_id='')
print(f"✅ Users WITH telegram_id: {users_with_telegram.count()}")

# Check users without telegram_id
users_without_telegram = User.objects.filter(telegram_id__isnull=True) | User.objects.filter(telegram_id='')
print(f"❌ Users WITHOUT telegram_id: {users_without_telegram.count()}")
print()

# Check cases
cases = Case.objects.all().select_related('user')
print(f"📋 Total cases in database: {cases.count()}")
print()

if cases.exists():
    print("📋 CASE DETAILS:")
    print("-" * 80)
    for case in cases:
        telegram_status = "✅" if case.user.telegram_id else "❌"
        case_num = case.user_case_number if case.user_case_number else case.id
        print(f"Case #{case_num} (DB ID: {case.id}): {case.title}")
        print(f"  User: {case.user.username}")
        print(f"  User telegram_id: {case.user.telegram_id or 'None'}")
        print(f"  Can receive notifications: {telegram_status}")
        print(f"  Status: {case.status}")
        print()

print("=" * 80)
print("🔧 DIAGNOSTICS:")
print("=" * 80)

# Users who need to /start the bot
users_need_start = User.objects.filter(role='user').filter(
    telegram_id__isnull=True
) | User.objects.filter(role='user').filter(telegram_id='')

if users_need_start.exists():
    print(f"\n⚠️  {users_need_start.count()} user(s) need to send /start to the bot:")
    for user in users_need_start:
        print(f"   - {user.username} ({user.email})")
    print("\n💡 Solution: These users must send /start to the bot on Telegram")
else:
    print("\n✅ All users have telegram_id - notifications should work!")

print()
print("=" * 80)
print("✅ CHECK COMPLETE!")
print("=" * 80)
