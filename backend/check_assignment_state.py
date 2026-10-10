#!/usr/bin/env python
"""
Diagnostic script to check assignment request state and email configuration
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User, Case, AssignmentRequest, CaseView, InternalChatView
from django.conf import settings

print("=" * 80)
print("ASSIGNMENT REQUEST & EMAIL DIAGNOSTIC")
print("=" * 80)

# Check email configuration
print("\n1. EMAIL CONFIGURATION:")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   FRONTEND_URL: {settings.FRONTEND_URL}")

# Check users and their emails
print("\n2. USER EMAIL ADDRESSES:")
users = User.objects.all()
for user in users:
    print(f"   {user.role.upper():8} | {user.username:20} | {user.email or '(no email)':40} | Verified: {user.email_verified} | Notifications: {user.email_notifications_enabled}")

# Check if owner and admins have SAME email (this is the problem!)
owner_emails = set(User.objects.filter(role='owner').values_list('email', flat=True))
admin_emails = set(User.objects.filter(role='admin').values_list('email', flat=True))
same_emails = owner_emails & admin_emails
if same_emails:
    print(f"\n   ⚠️  WARNING: Owner and admins share same email addresses: {same_emails}")
    print(f"   ⚠️  Emails sent from/to the same address are often blocked by mail servers!")

# Check assignment requests
print("\n3. ASSIGNMENT REQUESTS:")
requests = AssignmentRequest.objects.all().order_by('-created_at')
if not requests:
    print("   No assignment requests found")
else:
    for req in requests:
        print(f"   ID: {req.id} | Case: #{req.case.user_case_number} ({req.case.title[:30]}) | Admin: {req.admin.username} | Status: {req.status} | Created: {req.created_at}")

# Check pending vs processed
pending = AssignmentRequest.objects.filter(status='pending')
approved = AssignmentRequest.objects.filter(status='approved')
rejected = AssignmentRequest.objects.filter(status='rejected')

print(f"\n   Summary: {pending.count()} pending, {approved.count()} approved, {rejected.count()} rejected")

# Check specific case #8 issue
print("\n4. CASE #8 (Spiritual Growth) INVESTIGATION:")
try:
    case_8 = Case.objects.get(user_case_number=8)
    print(f"   Case #{case_8.user_case_number}: {case_8.title}")
    print(f"   Status: {case_8.status}")
    print(f"   Assigned Admin: {case_8.assigned_admin.username if case_8.assigned_admin else 'None'}")
    
    case_8_requests = AssignmentRequest.objects.filter(case=case_8).order_by('-created_at')
    if case_8_requests:
        print(f"   Assignment Requests for this case:")
        for req in case_8_requests:
            print(f"      - Request #{req.id}: Admin={req.admin.username}, Status={req.status}, Created={req.created_at}")
    else:
        print(f"   No assignment requests found for this case")
except Case.DoesNotExist:
    print("   Case #8 not found")

# Check CaseView and InternalChatView tables exist
print("\n5. SEEN STATUS TABLES:")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%view%'")
        tables = cursor.fetchall()
        print(f"   Tables found: {[t[0] for t in tables]}")
        
        # Check if tables exist and have data
        case_views_count = CaseView.objects.count()
        internal_views_count = InternalChatView.objects.count()
        print(f"   CaseView records: {case_views_count}")
        print(f"   InternalChatView records: {internal_views_count}")
        
        if case_views_count > 0:
            print(f"   Recent case views:")
            for view in CaseView.objects.all()[:5]:
                print(f"      - Case #{view.case.user_case_number} viewed by {view.user.username} at {view.viewed_at}")
except Exception as e:
    print(f"   ⚠️  Error checking seen status tables: {e}")

print("\n" + "=" * 80)
print("RECOMMENDATIONS:")
print("=" * 80)

if same_emails:
    print("\n❌ CRITICAL: Owner and admins share the same email address!")
    print("   → Email servers typically block/drop emails sent from an address to itself")
    print("   → Solution: Use DIFFERENT email addresses for owner and admin accounts")
    print("   → Or use a testing tool like MailHog/MailCatcher for development")

if pending.count() > 0:
    print(f"\n✅ {pending.count()} pending requests exist - UI should show these")

if case_8_requests.filter(status='pending').exists():
    print(f"\n⚠️  Case #8 has a PENDING request - this is why it shows in pending section!")
    print("   → The case may have multiple requests (one rejected, one pending)")

print("\n" + "=" * 80)
