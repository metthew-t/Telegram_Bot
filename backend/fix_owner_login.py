#!/usr/bin/env python
"""
Fix owner login issue - Reset password and verify email
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User
from django.contrib.auth import authenticate

print("\n" + "="*60)
print("🔧 FIXING OWNER LOGIN")
print("="*60 + "\n")

# Find or create owner
owner = User.objects.filter(username='owner').first()

if owner:
    print(f"✅ Found owner: {owner.username}")
    print(f"   Email: {owner.email}")
    print(f"   Email verified: {owner.email_verified}")
    print(f"   Role: {owner.role}")
else:
    print("⚠️  Owner not found! Creating new owner...")
    owner = User(username='owner', email='owner@example.com', role='owner')

# Reset password
owner.set_password('owner1234')
owner.email_verified = True  # Make sure email is verified
owner.save()

print(f"\n✅ Password reset to: owner1234")
print(f"✅ Email verified: {owner.email_verified}")

# Test authentication
print(f"\n🧪 Testing authentication...")
auth_user = authenticate(username='owner', password='owner1234')

if auth_user:
    print(f"✅ Authentication successful!")
    print(f"   Username: {auth_user.username}")
    print(f"   Role: {auth_user.role}")
    print(f"   Email verified: {auth_user.email_verified}")
    print(f"\n🎉 You can now login with:")
    print(f"   Username: owner")
    print(f"   Password: owner1234")
else:
    print(f"❌ Authentication failed! Something is wrong.")

print("\n" + "="*60 + "\n")
