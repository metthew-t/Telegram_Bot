#!/usr/bin/env python
"""
Fix stuck assignment requests that show as pending but were actually reviewed.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import AssignmentRequest, Case

print("=" * 80)
print("FIX STUCK ASSIGNMENT REQUESTS")
print("=" * 80)

# Find all assignment requests
all_requests = AssignmentRequest.objects.all().order_by('-created_at')
print(f"\nTotal assignment requests: {all_requests.count()}")

# Group by status
pending = all_requests.filter(status='pending')
approved = all_requests.filter(status='approved')
rejected = all_requests.filter(status='rejected')

print(f"  - Pending: {pending.count()}")
print(f"  - Approved: {approved.count()}")
print(f"  - Rejected: {rejected.count()}")

if pending.count() > 0:
    print("\n" + "=" * 80)
    print("PENDING REQUESTS:")
    print("=" * 80)
    
    for req in pending:
        case = req.case
        print(f"\nRequest ID: {req.id}")
        print(f"  Case: #{case.user_case_number} - {case.title}")
        print(f"  Admin: {req.admin.username}")
        print(f"  Created: {req.created_at}")
        print(f"  Status: {req.status}")
        print(f"  Case Status: {case.status}")
        print(f"  Case Assigned To: {case.assigned_admin.username if case.assigned_admin else 'None'}")
        
        # Check if this case is already assigned (meaning request should be approved/rejected)
        if case.status == 'assigned' and case.assigned_admin:
            if case.assigned_admin.id == req.admin.id:
                print(f"  ⚠️  ISSUE: Case is assigned to this admin but request is still pending!")
                print(f"  ✅ RECOMMENDATION: Mark as APPROVED")
                
                fix = input("     Do you want to auto-fix this? (yes/no): ").strip().lower()
                if fix == 'yes':
                    req.status = 'approved'
                    req.save()
                    print(f"     ✅ Fixed! Request marked as approved")
            else:
                print(f"  ⚠️  ISSUE: Case is assigned to DIFFERENT admin ({case.assigned_admin.username})")
                print(f"  ✅ RECOMMENDATION: Mark as REJECTED")
                
                fix = input("     Do you want to auto-fix this? (yes/no): ").strip().lower()
                if fix == 'yes':
                    req.status = 'rejected'
                    req.save()
                    print(f"     ✅ Fixed! Request marked as rejected")

print("\n" + "=" * 80)
print("CHECK COMPLETE")
print("=" * 80)

# Show summary again
pending_after = AssignmentRequest.objects.filter(status='pending').count()
print(f"\nPending requests remaining: {pending_after}")

if pending_after == 0:
    print("✅ All requests are properly processed!")
else:
    print(f"⚠️  {pending_after} request(s) still pending - may be legitimate new requests")
