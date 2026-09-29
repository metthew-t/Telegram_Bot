#!/usr/bin/env python3
"""
Auto-fix admin account on every deployment
This runs during build.sh and ensures admin login always works
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User

print("\n" + "=" * 60)
print("🔧 AUTO-FIX: Admin Account")
print("=" * 60)

try:
    # Get or create admin (owner role)
    admin, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'role': 'owner',
            'email_verified': True
        }
    )
    
    print(f"   Found admin: {admin.username} (ID: {admin.id})")
    print(f"   Before: email_verified={admin.email_verified}, role={admin.role}")
    
    # FORCE password reset - ALWAYS
    admin.set_password('admin1234')
    admin.email_verified = True
    admin.email = 'admin@example.com'
    admin.role = 'owner'
    admin.is_active = True
    admin.save(update_fields=['password', 'email_verified', 'email', 'role', 'is_active'])
    
    print(f"   After save: password RESET to admin1234")
    
    if created:
        print("✅ Created new admin account")
    else:
        print("✅ Updated existing admin account - PASSWORD RESET!")
    
    print(f"   Username: admin")
    print(f"   Password: admin1234 (CONFIRMED RESET)")
    print(f"   Email: {admin.email}")
    print(f"   Email verified: {admin.email_verified}")
    print("=" * 60 + "\n")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
