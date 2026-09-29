#!/usr/bin/env python3
"""
Delete old owner and create fresh admin account
Run this once to completely reset the owner account
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User

print("\n" + "=" * 60)
print("🔄 RESET: Deleting old owner & creating new admin")
print("=" * 60)

try:
    # Delete ALL existing owner accounts
    deleted_count = User.objects.filter(username='owner').delete()[0]
    if deleted_count > 0:
        print(f"🗑️  Deleted {deleted_count} old 'owner' account(s)")
    
    # Delete old admin if exists
    deleted_admin = User.objects.filter(username='admin').delete()[0]
    if deleted_admin > 0:
        print(f"🗑️  Deleted {deleted_admin} old 'admin' account(s)")
    
    # Create fresh admin account
    admin = User.objects.create(
        username='admin',
        email='admin@example.com',
        role='owner',
        email_verified=True,
        is_active=True
    )
    admin.set_password('admin1234')
    admin.save()
    
    print("✅ Created NEW admin account!")
    print(f"   Username: admin")
    print(f"   Password: admin1234")
    print(f"   Role: owner")
    print(f"   Email: {admin.email}")
    print(f"   Email verified: {admin.email_verified}")
    print(f"   ID: {admin.id}")
    print("=" * 60 + "\n")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
