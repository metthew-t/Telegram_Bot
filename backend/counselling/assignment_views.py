"""
Assignment Request Views - Completely rewritten from scratch
Handles admin assignment requests and owner approvals/rejections
"""
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings

from .models import CaseAssignmentRequest, Case, User, AuditLog
from .serializers import CaseAssignmentRequestSerializer
from .permissions import IsOwner
from .email_templates import render_assignment_request_email, render_assignment_approved_email
from .telegram_notifications import notify_case_user
from .email_notifications import _send_email


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
