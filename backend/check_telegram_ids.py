#!/usr/bin/env python
"""
Check all users' telegram_id values in the database
Run this to see which users have telegram_id and which don't
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User

print("\n" + "="*70)
print("📊 TELEGRAM ID CHECK - All Users")
print("="*70 + "\n")

all_users = User.objects.all()

if not all_users.exists():
    print("⚠️  No users found in database")
else:
    for user in all_users:
        print(f"👤 User: {user.username}")
        print(f"   Role: {user.role}")
        print(f"   Email: {user.email}")
        print(f"   Telegram ID: {user.telegram_id if user.telegram_id else '❌ NOT SET'}")
        print(f"   Type: {type(user.telegram_id)}")
        print(f"   Is None: {user.telegram_id is None}")
        print(f"   Is Empty: {user.telegram_id == ''}")
        print("-" * 70)

print("\n" + "="*70)
print("📋 SUMMARY")
print("="*70)
print(f"Total users: {all_users.count()}")
print(f"Users with telegram_id: {all_users.exclude(telegram_id__isnull=True).exclude(telegram_id='').count()}")
print(f"Users without telegram_id: {all_users.filter(telegram_id__isnull=True).count() + all_users.filter(telegram_id='').count()}")
print("="*70 + "\n")
