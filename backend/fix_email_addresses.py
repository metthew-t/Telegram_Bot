#!/usr/bin/env python
"""
Script to fix email addresses for owner and admin users.

IMPORTANT: Owner and admins currently share the same email (astucounselplatform@gmail.com)
This causes email notifications to fail because servers block emails sent from/to same address.

This script helps you update the email addresses to DIFFERENT values.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User

def main():
    print("=" * 80)
    print("FIX EMAIL ADDRESSES")
    print("=" * 80)
    print()
    print("⚠️  CRITICAL ISSUE: Owner and admins currently use the SAME email address!")
    print("   This causes email notifications to be blocked by mail servers.")
    print()
    print("Current email addresses:")
    print()
    
    # Show current emails
    users = User.objects.filter(role__in=['owner', 'admin']).order_by('role', 'username')
    for user in users:
        print(f"   {user.role.upper():8} | {user.username:20} | {user.email or '(no email)'}")
    
    print()
    print("=" * 80)
    print()
    print("This script will help you update to DIFFERENT email addresses.")
    print()
    
    # Ask if user wants to proceed
    proceed = input("Do you want to update email addresses now? (yes/no): ").strip().lower()
    if proceed != 'yes':
        print("Cancelled. No changes made.")
        return
    
    print()
    print("=" * 80)
    print("UPDATE EMAIL ADDRESSES")
    print("=" * 80)
    print()
    
    # Update owner emails
    owners = User.objects.filter(role='owner')
    print(f"Found {owners.count()} owner(s):")
    for i, owner in enumerate(owners, 1):
        print(f"\n{i}. Owner: {owner.username} (current: {owner.email})")
        new_email = input(f"   Enter NEW email for {owner.username} (or press Enter to skip): ").strip()
        if new_email:
            owner.email = new_email
            owner.email_verified = True  # Mark as verified
            owner.email_notifications_enabled = True
            owner.save()
            print(f"   ✅ Updated to: {new_email}")
        else:
            print(f"   ⏭️  Skipped")
    
    # Update admin emails
    admins = User.objects.filter(role='admin')
    print(f"\nFound {admins.count()} admin(s):")
    for i, admin in enumerate(admins, 1):
        print(f"\n{i}. Admin: {admin.username} (current: {admin.email})")
        new_email = input(f"   Enter NEW email for {admin.username} (or press Enter to skip): ").strip()
        if new_email:
            admin.email = new_email
            admin.email_verified = True  # Mark as verified
            admin.email_notifications_enabled = True
            admin.save()
            print(f"   ✅ Updated to: {new_email}")
        else:
            print(f"   ⏭️  Skipped")
    
    print()
    print("=" * 80)
    print("UPDATED EMAIL ADDRESSES")
    print("=" * 80)
    print()
    
    users = User.objects.filter(role__in=['owner', 'admin']).order_by('role', 'username')
    for user in users:
        print(f"   {user.role.upper():8} | {user.username:20} | {user.email or '(no email)'}")
    
    print()
    print("✅ Email addresses updated successfully!")
    print()
    print("NEXT STEPS:")
    print("1. Test email notifications by creating an assignment request")
    print("2. Check server logs for '[REQUEST] ✅' and '[APPROVE] ✅' messages")
    print("3. Verify emails are received at the new addresses")
    print()

if __name__ == '__main__':
    main()
