#!/usr/bin/env python
"""
Debug script to check assignment requests in the database
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import AssignmentRequest, Case, User

print("=" * 80)
print("ASSIGNMENT REQUESTS DATABASE CHECK")
print("=" * 80)

all_requests = AssignmentRequest.objects.all().order_by('-created_at')
print(f"\nTotal assignment requests in database: {all_requests.count()}\n")

pending = all_requests.filter(status='pending')
approved = all_requests.filter(status='approved')
rejected = all_requests.filter(status='rejected')

print(f"PENDING: {pending.count()}")
print(f"APPROVED: {approved.count()}")
print(f"REJECTED: {rejected.count()}")
print("\n" + "=" * 80)
print("ALL REQUESTS (most recent first):")
print("=" * 80)

for req in all_requests[:20]:  # Show last 20
    try:
        print(f"\nID: {req.id}")
        print(f"  Case: #{req.case.id} - {req.case.title}")
        print(f"  Admin: {req.admin.username}")
        print(f"  Status: {req.status}")
        print(f"  Created: {req.created_at}")
        print(f"  Reviewed: {req.reviewed_at}")
        print(f"  Reviewed by: {req.reviewed_by.username if req.reviewed_by else 'None'}")
    except Exception as e:
        print(f"  ERROR: {str(e)}")

print("\n" + "=" * 80)
print("PENDING REQUESTS DETAIL:")
print("=" * 80)

for req in pending:
    print(f"\nID: {req.id}")
    print(f"  Case: #{req.case.id} - {req.case.title}")
    print(f"  Case Status: {req.case.status}")
    print(f"  Case Assigned Admin: {req.case.assigned_admin.username if req.case.assigned_admin else 'None'}")
    print(f"  Requesting Admin: {req.admin.username}")
    print(f"  Request Status: {req.status}")
    print(f"  Created: {req.created_at}")
