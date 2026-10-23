#!/usr/bin/env python
"""Check both old and new assignment request tables"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import CaseAssignmentRequest, Case
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 80)
print("CHECKING ASSIGNMENT REQUEST TABLES")
print("=" * 80)

# Check NEW table (CaseAssignmentRequest)
print("\n1. NEW TABLE (CaseAssignmentRequest):")
print("-" * 80)
try:
    new_requests = CaseAssignmentRequest.objects.all().order_by('-requested_at')
    print(f"Total records: {new_requests.count()}")
    
    if new_requests.exists():
        for req in new_requests[:10]:
            print(f"  ID={req.id}, Case={req.case_id}, Admin={req.requesting_admin.username}, Status={req.status}, RequestedAt={req.requested_at}")
    else:
        print("  (empty)")
except Exception as e:
    print(f"  ERROR: {e}")

# Check OLD table (AssignmentRequest) - might still exist
print("\n2. OLD TABLE (AssignmentRequest) - checking if exists:")
print("-" * 80)
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='counselling_assignmentrequest';")
        old_table_exists = cursor.fetchone()
        
        if old_table_exists:
            print("  OLD TABLE EXISTS!")
            cursor.execute("SELECT COUNT(*) FROM counselling_assignmentrequest;")
            count = cursor.fetchone()[0]
            print(f"  Total records: {count}")
            
            if count > 0:
                cursor.execute("""
                    SELECT id, case_id, admin_id, status, created_at 
                    FROM counselling_assignmentrequest 
                    ORDER BY created_at DESC 
                    LIMIT 10;
                """)
                rows = cursor.fetchall()
                print("\n  Recent records:")
                for row in rows:
                    print(f"    ID={row[0]}, Case={row[1]}, AdminID={row[2]}, Status={row[3]}, CreatedAt={row[4]}")
        else:
            print("  Old table doesn't exist (good!)")
except Exception as e:
    print(f"  ERROR: {e}")

# Check pending cases
print("\n3. CASES WITH PENDING STATUS:")
print("-" * 80)
open_cases = Case.objects.filter(status='open').count()
assigned_cases = Case.objects.filter(status='assigned').count()
print(f"  Open cases: {open_cases}")
print(f"  Assigned cases: {assigned_cases}")

print("\n" + "=" * 80)
