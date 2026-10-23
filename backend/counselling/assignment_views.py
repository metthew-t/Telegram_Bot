"""
Assignment Request Views - Completely rewritten from scratch
Handles admin assignment requests and owner approvals/rejections
"""
import os
import requests
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

from .models import CaseAssignmentRequest, Case, User, AuditLog
from .serializers import CaseAssignmentRequestSerializer
from .email_templates import render_assignment_request_email, render_assignment_approved_email


class IsOwner(permissions.BasePermission):
    """Permission class: only users with role='owner' can access"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'owner')


def send_telegram_notification(telegram_id, text):
    """Send a Telegram notification to a specific user"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        return False
    
    telegram_id = str(telegram_id).strip() if telegram_id else None
    if not telegram_id or telegram_id == 'None':
        print(f"ERROR: Invalid telegram_id: {telegram_id}")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": telegram_id, "text": text}
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"ERROR: Telegram API Error: {response.status_code} - {response.text}")
            return False
        return True
    except Exception as e:
        print(f"ERROR: Telegram notification failed: {str(e)}")
        return False


def notify_case_user(case, text):
    """Notify case user via Telegram"""
    if not case.user.telegram_id:
        print(f"Backend Warning: Case #{case.id} user has no telegram_id.")
        return
    send_telegram_notification(case.user.telegram_id, text)


def _send_email(subject, html_body, text_body, recipients):
    """Send email via Brevo API"""
    if not recipients:
        print("[Email] No recipients, skipping")
        return
    
    api_key = os.getenv('BREVO_API_KEY')
    if not api_key:
        print("[Email] BREVO_API_KEY not set, skipping email")
        return
    
    from_email_str = settings.DEFAULT_FROM_EMAIL
    if '<' in from_email_str:
        sender_name = from_email_str.split('<')[0].strip()
        sender_email = from_email_str.split('<')[1].strip('>')
        from_dict = {"email": sender_email, "name": sender_name}
    else:
        from_dict = {"email": from_email_str}
    
    headers = {
        'api-key': api_key,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    data = {
        "sender": from_dict,
        "to": [{"email": email} for email in recipients],
        "subject": subject,
        "htmlContent": html_body,
        "textContent": text_body
    }
    
    try:
        response = requests.post('https://api.brevo.com/v3/smtp/email', headers=headers, json=data, timeout=10)
        if response.ok:
            print(f"[Email] ✅ Sent '{subject}' to {len(recipients)} recipient(s)")
        else:
            print(f"[Email] ❌ Brevo API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[Email] ❌ Exception: {e}")


class CaseAssignmentRequestViewSet(viewsets.ModelViewSet):
    """
    Completely rewritten assignment request system
    - Admin requests assignment for an open case
    - Owner sees pending requests
    - Owner approves (assigns case) or rejects
    - Email notifications sent to all parties
    """
    queryset = CaseAssignmentRequest.objects.select_related(
        'case', 'requesting_admin', 'reviewed_by'
    ).all()
    serializer_class = CaseAssignmentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']  # No PUT/PATCH/DELETE
    
    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        if user.role == 'owner':
            return self.queryset  # Owners see all requests
        elif user.role == 'admin':
            return self.queryset.filter(requesting_admin=user)  # Admins see only theirs
        return self.queryset.none()
    
    def create(self, request):
        """Admin creates new assignment request"""
        # Validate user is admin
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can request case assignments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate case_id provided
        case_id = request.data.get('case_id')
        if not case_id:
            return Response(
                {'error': 'case_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get case
        try:
            case = Case.objects.get(id=case_id)
        except Case.DoesNotExist:
            return Response(
                {'error': 'Case not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if case already assigned
        if case.status == 'assigned' and case.assigned_admin:
            return Response(
                {'error': 'This case is already assigned'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing pending request for this case
        existing = CaseAssignmentRequest.objects.filter(
            case=case,
            status=CaseAssignmentRequest.STATUS_PENDING
        ).first()
        
        if existing:
            return Response(
                {'error': f'A pending request already exists from {existing.requesting_admin.username}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new request
        assignment_req = CaseAssignmentRequest.objects.create(
            case=case,
            requesting_admin=request.user,
            status=CaseAssignmentRequest.STATUS_PENDING
        )
        
        print(f"[NEW_REQUEST] ID={assignment_req.id}, Case={case.id}, Admin={request.user.username}")
        
        # Send email to owners
        self._notify_owners_new_request(assignment_req)
        
        serializer = self.serializer_class(assignment_req)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def approve(self, request, pk=None):
        """Owner approves assignment request"""
        assignment_req = self.get_object()
        
        # Validate status is pending
        if assignment_req.status != CaseAssignmentRequest.STATUS_PENDING:
            return Response(
                {'error': f'Request already {assignment_req.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update request status
        assignment_req.status = CaseAssignmentRequest.STATUS_APPROVED
        assignment_req.reviewed_at = timezone.now()
        assignment_req.reviewed_by = request.user
        assignment_req.save()
        
        # Assign case to admin
        case = assignment_req.case
        case.assigned_admin = assignment_req.requesting_admin
        case.status = 'assigned'
        case.assigned_at = timezone.now()
        case.save()
        
        print(f"[APPROVED] Request={assignment_req.id}, Case={case.id} assigned to {assignment_req.requesting_admin.username}")
        
        # Create audit log
        AuditLog.objects.create(
            case=case,
            performer=request.user,
            action='assigned',
            details=f'Approved assignment - assigned to {assignment_req.requesting_admin.username}'
        )
        
        # Notify user via Telegram
        try:
            notify_case_user(case, f'Your case #{case.user_case_number} has been assigned to support.')
        except Exception as e:
            print(f"[APPROVED] Telegram error: {str(e)}")
        
        # Email admin
        self._notify_admin_approved(assignment_req)
        
        serializer = self.serializer_class(assignment_req)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def reject(self, request, pk=None):
        """Owner rejects assignment request"""
        assignment_req = self.get_object()
        
        # Validate status is pending
        if assignment_req.status != CaseAssignmentRequest.STATUS_PENDING:
            return Response(
                {'error': f'Request already {assignment_req.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update request status
        assignment_req.status = CaseAssignmentRequest.STATUS_REJECTED
        assignment_req.reviewed_at = timezone.now()
        assignment_req.reviewed_by = request.user
        assignment_req.save()
        
        print(f"[REJECTED] Request={assignment_req.id}")
        
        serializer = self.serializer_class(assignment_req)
        return Response(serializer.data)
    
    # Helper methods
    def _notify_owners_new_request(self, assignment_req):
        """Send email to owners about new assignment request"""
        try:
            owners = User.objects.filter(
                role='owner',
                email_verified=True,
                email_notifications_enabled=True
            )
            
            if not owners.exists():
                print(f"[EMAIL] No owners to notify")
                return
            
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
            
            for owner in owners:
                if owner.email:
                    subject, html_body, text_body = render_assignment_request_email(
                        assignment_req, frontend_url
                    )
                    _send_email(subject, html_body, text_body, [owner.email])
                    print(f"[EMAIL] Sent to owner: {owner.email}")
        except Exception as e:
            print(f"[EMAIL] Owner notification error: {str(e)}")
    
    def _notify_admin_approved(self, assignment_req):
        """Send email to admin about approval"""
        try:
            admin = assignment_req.requesting_admin
            
            if not (admin.email and admin.email_verified and admin.email_notifications_enabled):
                print(f"[EMAIL] Admin email not configured")
                return
            
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
            subject, html_body, text_body = render_assignment_approved_email(
                assignment_req, frontend_url
            )
            _send_email(subject, html_body, text_body, [admin.email])
            print(f"[EMAIL] Sent approval to admin: {admin.email}")
        except Exception as e:
            print(f"[EMAIL] Admin notification error: {str(e)}")
