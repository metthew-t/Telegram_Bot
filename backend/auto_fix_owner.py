#!/usr/bin/env python3
"""
Auto-fix owner account on every deployment
This runs during build.sh and ensures owner login always works
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User

print("\n" + "=" * 60)
print("🔧 AUTO-FIX: Owner Account")
print("=" * 60)

try:
    # Get or create owner
    owner, created = User.objects.get_or_create(
        username='owner',
        defaults={
            'email': 'owner@example.com',
            'role': 'owner',
            'email_verified': True
        }
    )
    
    # Always reset password and verify email
    owner.set_password('owner1234')
    owner.email_verified = True
    owner.email = 'owner@example.com'
    owner.role = 'owner'
    owner.is_active = True
    owner.save()
    
    if created:
        print("✅ Created new owner account")
    else:
        print("✅ Updated existing owner account")
    
    print(f"   Username: owner")
    print(f"   Password: owner1234")
    print(f"   Email: {owner.email}")
    print(f"   Email verified: {owner.email_verified}")
    print("=" * 60 + "\n")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
