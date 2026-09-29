"""
Django management command to run diagnostics
Usage: python manage.py run_diagnostics
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from counselling.models import User, Case, Message
from counselling.views import send_telegram_notification
import os
import requests


class Command(BaseCommand):
    help = 'Run complete diagnostics for login and notifications'

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write("🔍 COMPLETE DIAGNOSTIC")
        self.stdout.write("=" * 80)
        
        # Issue 1: Owner Login
        self.stdout.write("\n📋 ISSUE 1: OWNER LOGIN")
        self.stdout.write("-" * 80)
        
        owner = User.objects.filter(username='owner').first()
        
        if not owner:
            self.stdout.write(self.style.ERROR("❌ NO OWNER EXISTS - Creating..."))
            owner = User(username='owner', email='owner@example.com', role='owner')
            owner.set_password('owner1234')
            owner.email_verified = True
            owner.save()
            self.stdout.write(self.style.SUCCESS("✅ Created owner: owner / owner1234"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Owner exists: {owner.username}"))
            self.stdout.write(f"   Email: {owner.email}")
            self.stdout.write(f"   Email verified: {owner.email_verified}")
            
        # Test authentication
        test_user = authenticate(username='owner', password='owner1234')
        if test_user:
            self.stdout.write(self.style.SUCCESS("✅ Authentication WORKS!"))
        else:
            self.stdout.write(self.style.ERROR("❌ Authentication FAILS - Fixing..."))
            owner.set_password('owner1234')
            owner.email_verified = True
            owner.save()
            self.stdout.write(self.style.SUCCESS("✅ Fixed! Password: owner1234"))
        
        # Issue 2: Telegram Notifications
        self.stdout.write("\n📋 ISSUE 2: TELEGRAM NOTIFICATIONS")
        self.stdout.write("-" * 80)
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.stdout.write(f"Bot Token: {bot_token[:20] if bot_token else 'MISSING'}...")
        
        users = User.objects.filter(role='user')
        with_telegram = users.exclude(telegram_id__isnull=True).exclude(telegram_id='')
        without_telegram = users.filter(telegram_id__isnull=True) | users.filter(telegram_id='')
        
        self.stdout.write(f"\n👥 Users: {users.count()} total")
        self.stdout.write(self.style.SUCCESS(f"   ✅ With telegram_id: {with_telegram.count()}"))
        self.stdout.write(self.style.WARNING(f"   ⚠️ Without telegram_id: {without_telegram.count()}"))
        
        if without_telegram.exists():
            self.stdout.write("\n⚠️ Users need to /start bot:")
            for u in without_telegram:
                self.stdout.write(f"   - {u.username}")
        
        # Test notification
        if with_telegram.exists():
            self.stdout.write("\n🧪 TESTING NOTIFICATION...")
            test_user = with_telegram.first()
            self.stdout.write(f"Testing for: {test_user.username}")
            self.stdout.write(f"Telegram ID: {test_user.telegram_id}")
            
            success = send_telegram_notification(
                test_user.telegram_id,
                "🧪 Test from diagnostic - If you see this, notifications work!"
            )
            
            if success:
                self.stdout.write(self.style.SUCCESS("✅ NOTIFICATION SENT!"))
            else:
                self.stdout.write(self.style.ERROR("❌ NOTIFICATION FAILED!"))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("✅ DIAGNOSTIC COMPLETE")
        self.stdout.write("=" * 80)
