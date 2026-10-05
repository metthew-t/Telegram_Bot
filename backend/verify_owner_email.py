#!/usr/bin/env python
"""
Script to check and auto-verify owner emails.
This ensures owners can receive email notifications.
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User

def main():
    print("=" * 60)
    print("Owner Email Verification Check")
    print("=" * 60)
    
    owners = User.objects.filter(role='owner')
    
    if not owners.exists():
        print("❌ No owners found in database")
        return
    
    print(f"\nFound {owners.count()} owner(s):\n")
    
    for owner in owners:
        print(f"Owner: {owner.username} (ID: {owner.id})")
        print(f"  Email: {owner.email or '(not set)'}")
        print(f"  Email Verified: {owner.email_verified}")
        
        # Auto-verify owner emails that are not empty
        if owner.email and not owner.email_verified:
            print(f"  🔧 Auto-verifying email for owner {owner.username}...")
            owner.email_verified = True
            owner.save(update_fields=['email_verified'])
            print(f"  ✅ Email verified successfully")
        elif not owner.email:
            print(f"  ⚠️  No email set - cannot receive notifications")
        elif owner.email_verified:
            print(f"  ✅ Email already verified")
        
        print()
    
    print("=" * 60)
    print("Summary - Verified Owner Emails for Notifications:")
    print("=" * 60)
    
    verified_owners = User.objects.filter(
        role='owner',
        email_verified=True
    ).exclude(email='')
    
    if verified_owners.exists():
        print(f"\n✅ {verified_owners.count()} owner(s) can receive email notifications:\n")
        for owner in verified_owners:
            print(f"  • {owner.username}: {owner.email}")
    else:
        print("\n❌ No verified owner emails found!")
        print("   Owners will NOT receive email notifications.")
        print("   Please set and verify owner emails.")
    
    print()

if __name__ == '__main__':
    main()
