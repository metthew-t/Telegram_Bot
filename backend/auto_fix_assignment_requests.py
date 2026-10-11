#!/usr/bin/env python
"""
Automatically fix stuck assignment requests where:
- Request status is 'pending' 
- BUT the case is already assigned to an admin

This should run automatically to fix the "Beekumsa" issue.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import AssignmentRequest, Case
from django.utils import timezone

print("=" * 80)
print("AUTO-FIX STUCK ASSIGNMENT REQUESTS")
print("=" * 80)

# Find all pending requests
pending_requests = AssignmentRequest.objects.filter(status='pending').order_by('-created_at')

print(f"\nFound {pending_requests.count()} pending assignment requests")

fixed_count = 0

for req in pending_requests:
    case = req.case
    
    print(f"\n[CHECK] Request #{req.id}")
    print(f"  Case: #{case.user_case_number} - {case.title}")
    print(f"  Requesting Admin: {req.admin.username}")
    print(f"  Request Status: {req.status}")
    print(f"  Case Status: {case.status}")
    print(f"  Case Assigned To: {case.assigned_admin.username if case.assigned_admin else 'None'}")
    
    # Check if case is already assigned
    if case.status == 'assigned' and case.assigned_admin:
        # Case is assigned - this request should NOT be pending
        
        if case.assigned_admin.id == req.admin.id:
            # Case is assigned to the requesting admin - APPROVE the request
            print(f"  🔧 FIX: Case IS assigned to {req.admin.username} - marking request as APPROVED")
            req.status = 'approved'
            req.reviewed_at = timezone.now()
            req.save()
            fixed_count += 1
            print(f"  ✅ Fixed! Request #{req.id} marked as approved")
            
        else:
            # Case is assigned to a DIFFERENT admin - REJECT this request
            print(f"  🔧 FIX: Case assigned to DIFFERENT admin ({case.assigned_admin.username}) - marking request as REJECTED")
            req.status = 'rejected'
            req.reviewed_at = timezone.now()
            req.save()
            fixed_count += 1
            print(f"  ✅ Fixed! Request #{req.id} marked as rejected")
    else:
        print(f"  ✅ OK: Request is legitimately pending (case not yet assigned)")

print("\n" + "=" * 80)
print(f"FIX COMPLETE - Fixed {fixed_count} stuck request(s)")
print("=" * 80)

# Show final summary
pending_after = AssignmentRequest.objects.filter(status='pending').count()
approved_count = AssignmentRequest.objects.filter(status='approved').count()
rejected_count = AssignmentRequest.objects.filter(status='rejected').count()

print(f"\nFinal Status:")
print(f"  - Pending: {pending_after}")
print(f"  - Approved: {approved_count}")
print(f"  - Rejected: {rejected_count}")
