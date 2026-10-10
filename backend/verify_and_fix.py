#!/usr/bin/env python
"""
Verify and fix all issues:
1. Check if migration 0013 is applied
2. Check if CaseView and InternalChatView tables exist
3. Test email settings
4. Show assignment request statuses
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.db import connection
from counselling.models import AssignmentRequest, User

def check_tables():
    """Check if required tables exist"""
    print("\n" + "="*60)
    print("CHECKING DATABASE TABLES")
    print("="*60)
    
    with connection.cursor() as cursor:
        # Get all table names
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['counselling_caseview', 'counselling_internalchatview']
        
        for table in required_tables:
            if table in tables:
                print(f"✅ {table} EXISTS")
            else:
                print(f"❌ {table} MISSING - Migration 0013 not applied!")
        
        return all(table in tables for table in required_tables)

def check_assignment_requests():
    """Show assignment request statuses"""
    print("\n" + "="*60)
    print("ASSIGNMENT REQUESTS STATUS")
    print("="*60)
    
    requests = AssignmentRequest.objects.all().order_by('-created_at')[:10]
    
    for req in requests:
        status_emoji = "⏳" if req.status == 'pending' else ("✅" if req.status == 'approved' else "❌")
        print(f"{status_emoji} Request #{req.id}: Case #{req.case_id} - {req.status.upper()} - by {req.admin.username}")
    
    pending_count = AssignmentRequest.objects.filter(status='pending').count()
    print(f"\n📊 Total PENDING requests: {pending_count}")

def check_email_settings():
    """Check email configuration"""
    print("\n" + "="*60)
    print("EMAIL SETTINGS CHECK")
    print("="*60)
    
    from django.conf import settings
    
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    brevo_key = os.getenv('BREVO_API_KEY', '')
    if brevo_key:
        print(f"✅ BREVO_API_KEY: {brevo_key[:20]}...")
    else:
        print("❌ BREVO_API_KEY not set!")

def check_owner_email_settings():
    """Check if owner has email notifications enabled"""
    print("\n" + "="*60)
    print("OWNER EMAIL NOTIFICATION SETTINGS")
    print("="*60)
    
    owners = User.objects.filter(role='owner')
    
    for owner in owners:
        print(f"\nOwner: {owner.username}")
        print(f"  Email: {owner.email or 'NOT SET'}")
        print(f"  Email Verified: {owner.email_verified}")
        print(f"  Notifications Enabled: {owner.email_notifications_enabled}")
        
        if owner.email and owner.email_verified and owner.email_notifications_enabled:
            print(f"  ✅ Will receive emails")
        else:
            print(f"  ❌ Will NOT receive emails")

if __name__ == '__main__':
    print("\n🔍 SYSTEM VERIFICATION SCRIPT")
    
    tables_ok = check_tables()
    check_assignment_requests()
    check_email_settings()
    check_owner_email_settings()
    
    print("\n" + "="*60)
    if tables_ok:
        print("✅ DATABASE: All required tables exist")
    else:
        print("❌ DATABASE: Missing tables - Run migrations!")
    print("="*60)
