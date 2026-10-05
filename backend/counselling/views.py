import os
import uuid
import requests

from django.conf import settings
from django.db.models import Q
from django.contrib.auth import authenticate
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse

from .models import User, Case, Message, AuditLog, InternalMessage
from .serializers import UserSerializer, CaseSerializer, MessageSerializer, AuditLogSerializer, InternalMessageSerializer
from .email_templates import (
    render_verification_email,
    render_new_case_email,
    render_new_message_email,
    render_case_assigned_email,
    render_case_closed_email,
)
from .email_notifications import send_case_message_notification, send_internal_message_notification


# ─── Root ────────────────────────────────────────────────────────────────────

def api_root(request):
    """Diagnostic endpoint - shows system status"""
    from django.contrib.auth import authenticate
    import os
    
    # Check owner login
    owner = User.objects.filter(username='owner').first()
    owner_status = {
        'exists': owner is not None,
        'can_login': False,
        'email_verified': owner.email_verified if owner else False
    }
    
    if owner:
        test_auth = authenticate(username='owner', password='owner1234')
        owner_status['can_login'] = test_auth is not None
    
    # Check Telegram setup
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    users = User.objects.filter(role='user')
    users_with_telegram = users.exclude(telegram_id__isnull=True).exclude(telegram_id='')
    users_without_telegram = users.filter(telegram_id__isnull=True) | users.filter(telegram_id='')
    
    telegram_status = {
        'bot_token_set': bot_token is not None,
        'total_users': users.count(),
        'users_with_telegram_id': users_with_telegram.count(),
        'users_without_telegram_id': users_without_telegram.count(),
        'users_needing_start': [u.username for u in users_without_telegram]
    }
    
    return JsonResponse({
        "status": "online",
        "message": "Counselling Platform API is running",
        "diagnostics": {
            "owner_login": owner_status,
            "telegram_notifications": telegram_status
        },
        "recommendations": get_recommendations(owner_status, telegram_status)
    })

def get_recommendations(owner_status, telegram_status):
    """Generate recommendations based on diagnostic"""
    recs = []
    
    if not owner_status['can_login']:
        recs.append("⚠️ Owner login not working - redeploy to fix")
    
    if telegram_status['users_without_telegram_id'] > 0:
        recs.append(f"⚠️ {telegram_status['users_without_telegram_id']} user(s) need to send /start to bot")
    
    if not telegram_status['bot_token_set']:
        recs.append("❌ TELEGRAM_BOT_TOKEN not set in environment")
    
    if not recs:
        recs.append("✅ Everything looks good!")
    
    return recs



# ─── Telegram Notification Helpers ───────────────────────────────────────────

def send_telegram_notification(telegram_id, text):
    """Send a Telegram notification to a specific user"""
    print(f"\n[send_telegram_notification] CALLED")
    print(f"[send_telegram_notification] telegram_id param: {telegram_id} (type: {type(telegram_id)})")
    print(f"[send_telegram_notification] text length: {len(text)}")
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("ERROR: [send_telegram_notification] TELEGRAM_BOT_TOKEN not set in environment.")
        return False
    
    print(f"[send_telegram_notification] Bot token found: {token[:15]}...{token[-6:]}")

    # Ensure telegram_id is a string and not empty
    telegram_id = str(telegram_id).strip() if telegram_id else None
    if not telegram_id or telegram_id == 'None':
        print(f"ERROR: [send_telegram_notification] Invalid telegram_id after conversion: {telegram_id}")
        return False
    
    print(f"[send_telegram_notification] Final telegram_id: '{telegram_id}'")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text,
    }

    print(f"[send_telegram_notification] API URL: {url[:50]}...")
    print(f"[send_telegram_notification] Payload chat_id: {payload['chat_id']}")
    print(f"[send_telegram_notification] Sending HTTP POST request...")

    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"[send_telegram_notification] HTTP Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"ERROR: [send_telegram_notification] API Error: {response.status_code}")
            print(f"ERROR: [send_telegram_notification] Response body: {response.text}")
            
            # Parse common errors
            try:
                error_data = response.json()
                error_desc = error_data.get('description', '')
                print(f"ERROR: [send_telegram_notification] Error description: {error_desc}")
                
                if 'chat not found' in error_desc.lower():
                    print(f"ERROR: [send_telegram_notification] USER HASN'T STARTED BOT YET!")
                elif 'bot was blocked' in error_desc.lower():
                    print(f"ERROR: [send_telegram_notification] USER BLOCKED THE BOT!")
            except:
                pass
            
            return False
        
        print(f"SUCCESS: [send_telegram_notification] Message sent successfully!")
        response_data = response.json()
        print(f"SUCCESS: [send_telegram_notification] Message ID: {response_data.get('result', {}).get('message_id')}")
        return True
        
    except Exception as e:
        print(f"ERROR: [send_telegram_notification] Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def notify_case_user(case, text):
    if not case.user.telegram_id:
        print(f"Backend Warning: Case #{case.id} user has no telegram_id.")
        return
    send_telegram_notification(case.user.telegram_id, text)


def send_telegram_voice(telegram_id, voice_data, duration=None):
    """Send a voice message to a Telegram user"""
    print(f"\n[send_telegram_voice] CALLED")
    print(f"[send_telegram_voice] telegram_id: {telegram_id}")
    print(f"[send_telegram_voice] voice_data length: {len(voice_data) if voice_data else 0}")
    print(f"[send_telegram_voice] duration: {duration}s")
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ [send_telegram_voice] TELEGRAM_BOT_TOKEN not set")
        return False
    
    telegram_id = str(telegram_id).strip() if telegram_id else None
    if not telegram_id or telegram_id == 'None':
        print(f"❌ [send_telegram_voice] Invalid telegram_id: {telegram_id}")
        return False
    
    try:
        import base64
        import io
        
        # Decode base64 voice data
        voice_bytes = base64.b64decode(voice_data)
        print(f"[send_telegram_voice] Decoded voice bytes: {len(voice_bytes)}")
        
        # Telegram sendVoice API
        url = f"https://api.telegram.org/bot{token}/sendVoice"
        
        # Send as file upload
        files = {
            'voice': ('voice.ogg', io.BytesIO(voice_bytes), 'audio/ogg')
        }
        data = {
            'chat_id': telegram_id,
        }
        if duration:
            data['duration'] = duration
        
        print(f"[send_telegram_voice] Sending voice via Telegram API...")
        response = requests.post(url, data=data, files=files, timeout=30)
        
        print(f"[send_telegram_voice] HTTP Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ [send_telegram_voice] API Error: {response.text}")
            return False
        
        print(f"✅ [send_telegram_voice] Voice message sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ [send_telegram_voice] Exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def notify_staff(text):
    staff_users = User.objects.filter(role__in=['admin', 'owner']).exclude(telegram_id__isnull=True).exclude(telegram_id='')
    for user in staff_users:
        send_telegram_notification(user.telegram_id, text)

def notify_specific_users(users, text):
    for user in users:
        if getattr(user, 'telegram_id', None):
            send_telegram_notification(user.telegram_id, text)


# ─── Email Notification Helpers ──────────────────────────────────────────────

def _send_email(subject: str, html_body: str, text_body: str, recipients: list):
    """Send a multipart (HTML + plain text) email.
    
    Uses Brevo API when BREVO_API_KEY is available.
    Falls back to Django SMTP backend (configured via EMAIL_* env vars) otherwise.
    """
    print(f"[DEBUG] _send_email called with {len(recipients) if recipients else 0} recipients")
    
    if not recipients:
        print("[DEBUG] No recipients provided, skipping email")
        return
    
    print(f"[DEBUG] Recipients: {recipients}")
        
    api_key = os.getenv('BREVO_API_KEY')
    
    if api_key:
        # ── Brevo API path ──────────────────────────────────────────────────
        print(f"[DEBUG] BREVO_API_KEY found: {api_key[:15]}...{api_key[-6:]}")

        from_email_str = settings.DEFAULT_FROM_EMAIL
        print(f"[DEBUG] DEFAULT_FROM_EMAIL: {from_email_str}")
        
        if '<' in from_email_str:
            sender_name = from_email_str.split('<')[0].strip()
            sender_email = from_email_str.split('<')[1].strip('>')
            from_dict = {"email": sender_email, "name": sender_name}
        else:
            from_dict = {"email": from_email_str}
        
        print(f"[DEBUG] Parsed sender: {from_dict}")

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
        
        print(f"[DEBUG] Sending request to Brevo API...")
        
        try:
            response = requests.post('https://api.brevo.com/v3/smtp/email', headers=headers, json=data, timeout=10)
            print(f"[DEBUG] Brevo API response status: {response.status_code}")
            
            if response.ok:
                print(f"[Email] ✅ Sent '{subject}' to {len(recipients)} recipient(s) via Brevo.")
            else:
                print(f"[Email] ❌ Brevo API Error {response.status_code}: {response.text}")
                # Fallback to SMTP on Brevo failure
                print(f"[Email] Attempting SMTP fallback...")
                _send_email_smtp(subject, html_body, text_body, recipients)
        except Exception as exc:
            print(f"[Email] ❌ Exception while sending via Brevo: {exc}")
            print(f"[Email] Attempting SMTP fallback...")
            _send_email_smtp(subject, html_body, text_body, recipients)
    else:
        # ── SMTP fallback path ──────────────────────────────────────────────
        print(f"[Email] BREVO_API_KEY not set — falling back to SMTP backend.")
        _send_email_smtp(subject, html_body, text_body, recipients)


def _send_email_smtp(subject: str, html_body: str, text_body: str, recipients: list):
    """Send email via Django SMTP backend (EMAIL_HOST / EMAIL_HOST_USER etc. from env)."""
    try:
        from_email_str = settings.DEFAULT_FROM_EMAIL
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email_str,
            to=recipients,
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        print(f"[Email] ✅ Sent '{subject}' to {len(recipients)} recipient(s) via SMTP.")
    except Exception as exc:
        print(f"[Email] ❌ SMTP send failed: {exc}")



def _staff_email_recipients():
    """Return list of email addresses for all verified admins + owners."""
    return list(
        User.objects.filter(
            role__in=['admin', 'owner'],
            email_verified=True,
        ).exclude(email='').values_list('email', flat=True)
    )


def _owner_email_recipients():
    """Return list of email addresses for verified owners only."""
    return list(
        User.objects.filter(
            role='owner',
            email_verified=True,
        ).exclude(email='').values_list('email', flat=True)
    )


def _user_can_access_case(user, case):
    """
    Check if a user can access/modify a case.
    
    Rules:
    - Owners can access any case
    - Admins can only access cases assigned to them
    - OWNERS AS ONE ENTITY: Any owner can access cases assigned to any owner
    - Users can only access their own cases
    """
    if user.role == 'owner':
        return True
    
    if user.role == 'admin' and case.assigned_admin == user:
        return True
    
    # Allow any owner to access cases assigned to any owner
    if user.role == 'owner' and case.assigned_admin and case.assigned_admin.role == 'owner':
        return True
    
    if case.user == user:
        return True
    
    return False


def send_email_to_staff(subject: str, html_body: str, text_body: str):
    _send_email(subject, html_body, text_body, _staff_email_recipients())


def send_email_to_owners(subject: str, html_body: str, text_body: str):
    _send_email(subject, html_body, text_body, _owner_email_recipients())


def send_email_to_specific_users(subject: str, html_body: str, text_body: str, users):
    emails = []
    for user in users:
        if getattr(user, 'email_verified', False) and getattr(user, 'email', ''):
            emails.append(user.email)
    _send_email(subject, html_body, text_body, emails)


def send_verification_email(user, request):
    """Generate a UUID token, save it, and dispatch the formal verification email."""
    print(f"\n[DEBUG] send_verification_email called for user: {user.username}, email: {user.email}")
    
    token = uuid.uuid4()
    user.email_verification_token = token
    user.email_verified = False
    user.save(update_fields=['email_verification_token', 'email_verified'])
    
    print(f"[DEBUG] Token generated and saved: {token}")

    frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')
    backend_url = getattr(settings, 'BACKEND_URL', os.getenv('BACKEND_URL', 'http://localhost:8000')).rstrip('/')
    verification_link = f"{backend_url}/api/verify-email/?token={token}"

    print(f"\n\n{'='*60}\n[ACTION REQUIRED] VERIFICATION LINK FOR {user.username}:\n{verification_link}\n{'='*60}\n\n")

    subject, html_body, text_body = render_verification_email(user, verification_link)
    print(f"[DEBUG] Email rendered. Subject: {subject}")
    print(f"[DEBUG] Calling _send_email to: {user.email}")
    
    _send_email(subject, html_body, text_body, [user.email])


# ─── Permissions ─────────────────────────────────────────────────────────────

class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'owner')

class IsAdminOrOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner'])

class IsOwnerOrSelf(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return request.user.role == 'owner' or obj == request.user


# ─── Email Verification View ──────────────────────────────────────────────────

class EmailVerifyView(APIView):
    """
    GET /api/verify-email/?token=<uuid>
    Marks the matching user's email as verified and redirects to the frontend
    success page. Returns a JSON error if the token is invalid or missing.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token_str = request.query_params.get('token', '').strip()
        if not token_str:
            return Response({'error': 'Verification token is missing.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = uuid.UUID(token_str)
        except ValueError:
            return Response({'error': 'Invalid token format.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email_verification_token=token)
        except User.DoesNotExist:
            return Response({'error': 'Token not found or already used.'}, status=status.HTTP_404_NOT_FOUND)

        user.email_verified = True
        user.email_verification_token = None
        user.save(update_fields=['email_verified', 'email_verification_token'])

        frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')
        return redirect(f"{frontend_url}/email-verified")


# ─── User ViewSet ─────────────────────────────────────────────────────────────

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'list':
            return [IsOwner()]
        if self.action == 'retrieve':
            return [IsOwnerOrSelf()]
        if self.action == 'create':
            return [permissions.AllowAny()]
        if self.action == 'destroy':
            return [IsOwner()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.role == 'owner':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    def perform_create(self, serializer):
        requested_role = self.request.data.get('role', 'admin')
        email = self.request.data.get('email', '').strip().lower()
        
        # Check for duplicate email if email is provided
        if email:
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'email': f'An account with email {email} already exists. Please use a different email or use forgot password to reset your password.'
                })

        # If anonymous, only allow 'admin' or 'user'
        if not self.request.user.is_authenticated:
            role = 'admin' if requested_role in ['admin', 'owner'] else requested_role
            user = serializer.save(role=role)
        # If logged in as owner, respect whatever they sent and auto-verify
        elif self.request.user.role == 'owner':
            user = serializer.save()
            user.email_verified = True
            user.save(update_fields=['email_verified'])
        # Fallback for other cases
        else:
            user = serializer.save(role='admin')

        # Send email verification for admins/owners who provided an email (if not already verified)
        if user.role in ['admin', 'owner'] and user.email and not user.email_verified:
            try:
                send_verification_email(user, self.request)
            except Exception as exc:
                print(f"[Email] Verification email failed for {user.username}: {exc}")
        
        # ── Notify all existing owners when a new owner is created ──
        if user.role == 'owner' and self.request.user.is_authenticated:
            try:
                from .email_templates import render_new_owner_created_email
                frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')
                
                subject, html_body, text_body = render_new_owner_created_email(
                    user, 
                    self.request.user.username, 
                    frontend_url
                )
                
                # Collect all owner emails (existing owners + new owner)
                owner_emails = []
                existing_owners = User.objects.filter(role='owner', email_verified=True).exclude(id=user.id)
                for owner in existing_owners:
                    if owner.email:
                        owner_emails.append(owner.email)
                
                # Add new owner's email if verified
                if user.email and user.email_verified:
                    owner_emails.append(user.email)
                
                if owner_emails:
                    _send_email(subject, html_body, text_body, owner_emails)
                    print(f"[Email] ✅ New owner notification sent to {len(owner_emails)} owner(s)")
            except Exception as exc:
                print(f"[Email] Failed to send new owner notification: {exc}")


    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def verify(self, request, pk=None):
        """Owner can manually mark an admin/user as email-verified (useful when email delivery fails)."""
        user = self.get_object()
        user.email_verified = True
        user.email_verification_token = None
        user.save(update_fields=['email_verified', 'email_verification_token'])
        return Response({'status': 'verified'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request, pk=None):
        """Allow user to change their own password"""
        user = self.get_object()
        
        # Users can only change their own password (unless owner)
        if request.user.id != user.id and request.user.role != 'owner':
            return Response(
                {'error': 'You can only change your own password'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': 'Both old_password and new_password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify old password
        if not user.check_password(old_password):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        print(f"[PasswordChange] ✅ Password changed successfully for user: {user.username}")
        
        return Response({'status': 'success', 'message': 'Password changed successfully'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_email(self, request, pk=None):
        """Allow user to change their email (owners only or self)"""
        user = self.get_object()
        
        # Users can only change their own email (unless owner)
        if request.user.id != user.id and request.user.role != 'owner':
            return Response(
                {'error': 'You can only change your own email'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_email = request.data.get('email', '').strip().lower()
        
        if not new_email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, new_email):
            return Response(
                {'error': 'Invalid email format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if email already exists (excluding current user)
        if User.objects.filter(email=new_email).exclude(id=user.id).exists():
            return Response(
                {'error': 'This email is already in use'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update email and mark as unverified if email changed
        if user.email != new_email:
            user.email = new_email
            user.email_verified = False
            user.save(update_fields=['email', 'email_verified'])
            
            # Send verification email for new email
            try:
                send_verification_email(user, request)
                print(f"[EmailChange] ✅ Email changed for user {user.username}: {new_email}")
                return Response({
                    'status': 'success',
                    'message': 'Email updated successfully. Please check your inbox for verification email.',
                    'email': new_email,
                    'email_verified': False
                })
            except Exception as exc:
                print(f"[Email] Verification email failed: {exc}")
                return Response({
                    'status': 'success',
                    'message': 'Email updated but verification email failed to send. Contact support.',
                    'email': new_email,
                    'email_verified': False
                })
        
        return Response({
            'status': 'no_change',
            'message': 'Email is already set to this address'
        })

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny], url_path='resend-verification')
    def resend_verification(self, request):
        """Resend verification email. Accepts {'email': '...'} or {'username': '...'}."""
        email = request.data.get('email', '').strip()
        username = request.data.get('username', '').strip()

        user = None
        if email:
            user = User.objects.filter(email=email, role__in=['admin', 'owner']).first()
        elif username:
            user = User.objects.filter(username=username, role__in=['admin', 'owner']).first()

        if not user:
            return Response({'error': 'No admin/owner account found with that email or username.'}, status=status.HTTP_404_NOT_FOUND)

        if user.email_verified:
            return Response({'status': 'already_verified', 'message': 'This account is already verified. Please log in.'})

        if not user.email:
            return Response({'error': 'This account has no email address on file.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            send_verification_email(user, request)
            return Response({'status': 'sent', 'message': f'Verification email resent to {user.email}.'})
        except Exception as exc:
            return Response({'error': f'Failed to send verification email: {exc}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─── Case ViewSet ─────────────────────────────────────────────────────────────

class CaseViewSet(viewsets.ModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['destroy', 'delete']:
            return [IsOwner()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.role == 'owner':
            return Case.objects.all()
        if user.role == 'admin':
            # Admins can see all cases (for visibility in "All Available")
            # But they can only interact with assigned cases or request open cases
            return Case.objects.all()
        return Case.objects.filter(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        if self.request.user.role in ['owner', 'admin']:
            serializer.save(user=serializer.validated_data.get('user', self.request.user))
        else:
            case = serializer.save(user=self.request.user)
            frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')

            # ── Telegram ──
            notify_staff(
                f"🆕 *New Case Created*\n\n"
                f"🆔 ID: #{case.id}\n"
                f"📝 Title: {case.title}\n"
                f"👤 User: {self.request.user.username}"
            )

            # ── Email ──
            try:
                subject, html_body, text_body = render_new_case_email(case, frontend_url)
                send_email_to_owners(subject, html_body, text_body)  # Only notify owners
            except Exception as exc:
                print(f"[Email] New-case email failed: {exc}")

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrOwner])
    def assign(self, request, pk=None):
        from django.utils import timezone
        
        case = self.get_object()
        admin_id = request.data.get('admin_id')
        try:
            # Allow assignment to both admins and owners
            admin = User.objects.get(id=admin_id, role__in=['admin', 'owner'])
        except User.DoesNotExist:
            return Response({'error': 'User not found or invalid role'}, status=status.HTTP_400_BAD_REQUEST)

        # ── OWNERS AS ONE ENTITY: When assigning to any owner, assign to first owner (representative) ──
        actual_assigned_admin = admin
        if admin.role == 'owner':
            # Get the first owner as the representative for all owners
            first_owner = User.objects.filter(role='owner').order_by('id').first()
            if first_owner:
                actual_assigned_admin = first_owner
                print(f"[Assignment] Owner assignment: Assigning to first owner {first_owner.username} (represents all owners)")
        
        case.assigned_admin = actual_assigned_admin
        case.status = 'assigned'
        case.assigned_at = timezone.now()  # Track when assigned
        case.save()
        AuditLog.objects.create(
            case=case,
            performer=request.user,
            action='assigned',
            details=f'Assigned case to {"all owners" if actual_assigned_admin.role == "owner" else "admin " + actual_assigned_admin.username}',
        )
        notify_case_user(case, f'Your case #{case.user_case_number} has been assigned to support.')

        frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')

        # ── Email: notify the assigned admin/owner + all owners ──
        try:
            display_name = "All Owners" if actual_assigned_admin.role == 'owner' else actual_assigned_admin.username
            subject, html_body, text_body = render_case_assigned_email(
                case, display_name, request.user.username, frontend_url
            )
            # Collect verified emails: assigned admin + all owners
            recipients = []
            if actual_assigned_admin.role == 'admin' and actual_assigned_admin.email and actual_assigned_admin.email_verified:
                recipients.append(actual_assigned_admin.email)
            elif actual_assigned_admin.role == 'owner':
                # Notify all owners
                owner_emails = _owner_email_recipients()
                recipients.extend(owner_emails)
            else:
                # Also include owner emails for visibility
                owner_emails = _owner_email_recipients()
                recipients.extend(e for e in owner_emails if e not in recipients)
            
            if recipients:
                _send_email(subject, html_body, text_body, recipients)
        except Exception as exc:
            print(f"[Email] Case-assigned email failed: {exc}")

        return Response({'status': 'assigned'})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        from django.utils import timezone
        
        case = self.get_object()
        if not _user_can_access_case(request.user, case):
            return Response(
                {'error': 'You do not have permission to close this case'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        case.status = 'closed'
        case.closed_at = timezone.now()  # Track when closed
        case.save()
        AuditLog.objects.create(
            case=case,
            performer=request.user,
            action='closed',
            details=f'Case closed by {request.user.username}',
        )
        
        # Send feedback request to user via Telegram with inline button
        feedback_message = (
            f"Your case #{case.user_case_number} ({case.title}) has been closed.\n\n"
            f"📝 Please share your feedback about your counselor and experience.\n"
            f"Your feedback helps us improve our service.\n\n"
            f"Click the button below to submit your feedback."
        )
        
        # Create inline keyboard with feedback button (JSON format for Telegram API)
        inline_keyboard = [[{"text": "📝 Submit Feedback", "callback_data": f"feedback_{case.id}"}]]
        
        # Send message with inline button via Telegram API
        if case.user.telegram_id:
            try:
                import requests
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {
                    "chat_id": str(case.user.telegram_id),
                    "text": feedback_message,
                    "reply_markup": {
                        "inline_keyboard": inline_keyboard
                    }
                }
                print(f"[Feedback] Sending feedback button to Telegram user {case.user.telegram_id}")
                print(f"[Feedback] Payload: {payload}")
                response = requests.post(url, json=payload, timeout=10)
                print(f"[Feedback] Telegram API response: {response.status_code}")
                print(f"[Feedback] Response body: {response.text}")
                if response.status_code != 200:
                    print(f"[Feedback] ❌ Failed to send feedback button: {response.text}")
                    # Fallback to simple message
                    notify_case_user(case, feedback_message)
                else:
                    print(f"[Feedback] ✅ Feedback button sent successfully")
            except Exception as e:
                print(f"[Feedback] ❌ Exception while sending feedback button: {e}")
                # Fallback to simple message
                notify_case_user(case, feedback_message)

        frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')

        # ── Email: notify only assigned admin + owners ──
        try:
            subject, html_body, text_body = render_case_closed_email(case, request.user.username, frontend_url)
            
            # Collect recipients: only assigned admin (if exists) + all owners
            recipients = []
            
            # Add assigned admin's email if verified
            if case.assigned_admin and case.assigned_admin.email and case.assigned_admin.email_verified:
                if case.assigned_admin.role == 'admin':  # Don't duplicate if admin is also owner
                    recipients.append(case.assigned_admin.email)
            
            # Add all owner emails
            owner_emails = _owner_email_recipients()
            recipients.extend(e for e in owner_emails if e not in recipients)
            
            if recipients:
                _send_email(subject, html_body, text_body, recipients)
                print(f"[Email] Case closed notification sent to {len(recipients)} recipient(s)")
        except Exception as exc:
            print(f"[Email] Case-closed email failed: {exc}")

        return Response({'status': 'closed'})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark case as resolved (before closing)"""
        from django.utils import timezone
        
        case = self.get_object()
        if not _user_can_access_case(request.user, case):
            return Response(
                {'error': 'You do not have permission to resolve this case'},
                status=status.HTTP_FORBIDDEN
            )
        
        case.status = 'resolved'
        case.resolved_at = timezone.now()  # Track when resolved
        case.save()
        AuditLog.objects.create(
            case=case,
            performer=request.user,
            action='resolved',
            details=f'Case marked as resolved by {request.user.username}',
        )
        notify_case_user(case, f'Your case #{case.user_case_number} has been resolved.')
        return Response({'status': 'resolved'})


# ─── Message ViewSet ──────────────────────────────────────────────────────────

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Message.objects.all()
        case_id = self.request.query_params.get('case')
        if user.role == 'owner':
            if case_id:
                return queryset.filter(case_id=case_id)
            return queryset
        if user.role == 'admin':
            # Admins can see messages from cases assigned to them OR all open cases
            queryset = queryset.filter(
                Q(case__assigned_admin=user) | Q(case__status='open')
            )
        else:
            queryset = queryset.filter(case__user=user)
        if case_id:
            queryset = queryset.filter(case_id=case_id)
        return queryset


    def perform_create(self, serializer):
        case = serializer.validated_data['case']
        user = self.request.user
        
        # ENHANCED LOGGING FOR DEBUGGING
        print(f"\n{'='*80}")
        print(f"[MESSAGE CREATE] New message being created")
        print(f"[MESSAGE CREATE] Sender: {user.username} (Role: {user.role}, ID: {user.id})")
        print(f"[MESSAGE CREATE] Case ID: {case.id}")
        print(f"[MESSAGE CREATE] Case user: {case.user.username} (ID: {case.user.id})")
        print(f"[MESSAGE CREATE] Case user telegram_id: {case.user.telegram_id}")
        print(f"[MESSAGE CREATE] Case assigned_admin: {case.assigned_admin}")
        print(f"{'='*80}\n")
        
        allowed = _user_can_access_case(user, case)
        
        print(f"[PERMISSION CHECK] User role: {user.role}")
        print(f"[PERMISSION CHECK] Is owner: {user.role == 'owner'}")
        print(f"[PERMISSION CHECK] Is assigned admin: {user.role == 'admin' and case.assigned_admin == user}")
        print(f"[PERMISSION CHECK] Is case user: {case.user == user}")
        print(f"[PERMISSION CHECK] Allowed: {allowed}\n")
        
        if not allowed:
            print(f"[PERMISSION DENIED] User {user.username} not allowed to message case #{case.id}")
            raise PermissionDenied('Permission denied')

        message = serializer.save(sender=user)
        print(f"[MESSAGE SAVED] Message ID: {message.id}, Content length: {len(message.content)}\n")
        
        # Send email notification for case messages
        try:
            send_case_message_notification(case, message, user)
        except Exception as e:
            print(f"[EMAIL NOTIFICATION] Error sending case message notification: {e}")
        
        frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')

        if user.role in ['admin', 'owner']:
            # Admin/Owner replied - Notify case user via Telegram
            try:
                print(f"{'='*80}")
                print(f"[TELEGRAM NOTIFICATION] Admin/Owner {user.username} replied to case #{case.id}")
                print(f"[TELEGRAM NOTIFICATION] Case user: {case.user.username}")
                print(f"[TELEGRAM NOTIFICATION] Case user telegram_id: {case.user.telegram_id}")
                print(f"[TELEGRAM NOTIFICATION] Message type: {message.message_type}")
                print(f"[TELEGRAM NOTIFICATION] telegram_id type: {type(case.user.telegram_id)}")
                print(f"{'='*80}")
                
                if case.user.telegram_id:
                    telegram_id_str = str(case.user.telegram_id).strip()
                    print(f"[TELEGRAM NOTIFICATION] Converted telegram_id to string: '{telegram_id_str}'")
                    print(f"[TELEGRAM NOTIFICATION] Preparing notification...")
                    
                    # Check if it's a voice message
                    if message.message_type == 'voice' and message.voice_data:
                        print(f"[TELEGRAM NOTIFICATION] Sending VOICE message to Telegram...")
                        success = send_telegram_voice(
                            telegram_id_str, 
                            message.voice_data, 
                            message.voice_duration
                        )
                        
                        if success:
                            print(f"[TELEGRAM NOTIFICATION] SUCCESS: Voice message sent successfully")
                        else:
                            print(f"[TELEGRAM NOTIFICATION] ERROR: Failed to send voice message")
                            # Fallback: send text notification
                            case_num = case.user_case_number if case.user_case_number else case.id
                            fallback_text = f'Voice message on your case #{case_num}: {case.title}\n\nPlease check the website to listen.'
                            send_telegram_notification(telegram_id_str, fallback_text)
                    else:
                        # Regular text message
                        case_num = case.user_case_number if case.user_case_number else case.id
                        notification_text = f'New response on your case #{case_num}: {case.title}\n\n{message.content[:500]}'
                        safe_print_text = notification_text.encode('ascii', 'ignore').decode('ascii')
                        print(f"[TELEGRAM NOTIFICATION] Notification text preview: {safe_print_text[:100]}...")
                        print(f"[TELEGRAM NOTIFICATION] Calling send_telegram_notification()...")
                        
                        success = send_telegram_notification(telegram_id_str, notification_text)
                        
                        if success:
                            print(f"[TELEGRAM NOTIFICATION] SUCCESS: Notification sent successfully to case user")
                        else:
                            print(f"[TELEGRAM NOTIFICATION] ERROR: Failed to send notification to case user")
                else:
                    print(f"[TELEGRAM NOTIFICATION] WARNING: Case user has no telegram_id (value is: {case.user.telegram_id})")
                    print(f"[TELEGRAM NOTIFICATION] WARNING: Notification NOT sent - user needs to /start the bot")
            except Exception as telegram_exc:
                print(f"[TELEGRAM NOTIFICATION] CRITICAL EXCEPTION in notification block: {telegram_exc}")
                import traceback
                traceback.print_exc()

            # Email owners for oversight (admin replied)
            try:
                subject, html_body, text_body = render_new_message_email(
                    case, message, user.username, frontend_url
                )
                send_email_to_owners(subject, html_body, text_body)
            except Exception as exc:
                print(f"[Email] Admin-reply email failed: {exc}")
        else:
            # Client replied — determine who to notify
            if case.status == 'assigned' and case.assigned_admin:
                # Notify only assigned admin and all owners
                owners = list(User.objects.filter(role='owner'))
                notified_users = list(set([case.assigned_admin] + owners))
            else:
                # Notify all staff
                notified_users = list(User.objects.filter(role__in=['admin', 'owner']))

            notify_specific_users(
                notified_users,
                f"💬 New message on case #{case.id}\n"
                f"👤 From: {user.username}\n\n"
                f"{message.content}"
            )

            # Email the selected staff members
            try:
                subject, html_body, text_body = render_new_message_email(
                    case, message, user.username, frontend_url
                )
                send_email_to_specific_users(subject, html_body, text_body, notified_users)
            except Exception as exc:
                print(f"[Email] New-message email failed: {exc}")

        AuditLog.objects.create(
            case=case,
            performer=user,
            action='reply' if user.role in ['admin', 'owner'] else 'submitted',
            details=f'Message created by {user.username}: {message.content[:120]}',
        )


# ─── Audit Log ViewSet ────────────────────────────────────────────────────────

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-created_at')
    serializer_class = AuditLogSerializer
    permission_classes = [IsOwner]


# ─── Auth Views ───────────────────────────────────────────────────────────────

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            # Exempt the main 'owner' username from email verification so you can always log in
            needs_verification = user.role in ['admin', 'owner'] and not user.email_verified
            if needs_verification and user.username != 'owner':
                return Response({'error': 'Please verify your email address before logging in. Check your inbox for the verification link.'}, status=status.HTTP_403_FORBIDDEN)
                
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class TelegramLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        telegram_id = str(request.data.get('telegram_id') or '').strip()
        username = request.data.get('username') or f'telegram_{telegram_id[-10:]}'
        if not telegram_id:
            return Response({'error': 'telegram_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(telegram_id=telegram_id).first()
        if user is None:
            base_username = username[:140]
            generated_username = base_username
            suffix = 1
            while User.objects.filter(username=generated_username).exists():
                generated_username = f'{base_username}_{suffix}'
                suffix += 1

            user = User(username=generated_username, telegram_id=telegram_id, role='user')
            user.set_unusable_password()
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
        })


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        """Update profile including profile photo"""
        user = request.user
        
        # Only allow admins and owners to upload profile photos
        if 'profile_photo' in request.data:
            if user.role not in ['admin', 'owner']:
                return Response(
                    {'error': 'Only admins and owners can upload profile photos'},
                    status=status.HTTP_403_FORBIDDEN
                )
            user.profile_photo = request.data.get('profile_photo')
        
        # Allow other profile updates
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServerInfoView(APIView):
    """
    GET /api/server-info/
    Returns server IP address and other debug info (owner only)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'owner':
            return Response(
                {'error': 'Only owners can view server info'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get server's outbound IP by making a request to a service
        try:
            import requests
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            server_ip = response.json().get('ip', 'Unable to detect')
        except Exception as e:
            server_ip = f'Error: {str(e)}'
        
        # Check Brevo API status
        brevo_api_key = os.getenv('BREVO_API_KEY')
        brevo_status = 'Configured' if brevo_api_key else 'Not configured'
        
        info = {
            'server_ip': server_ip,
            'brevo_api_key_status': brevo_status,
            'smtp_host': os.getenv('EMAIL_HOST', 'Not configured'),
            'smtp_user': os.getenv('EMAIL_HOST_USER', 'Not configured'),
            'default_from_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        return Response(info)


# ─── Password Reset Views ─────────────────────────────────────────────────────

class ForgotPasswordView(APIView):
    """
    POST /api/forgot-password/
    Request password reset - sends email with reset link
    Body: { "email": "admin@example.com" }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .models import PasswordResetToken
        from .email_templates import render_password_reset_email
        
        email = request.data.get('email', '').strip().lower()
        
        if not email:
            return Response(
                {'error': 'Email is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find user by email (only admins and owners can reset password)
        # Use filter().first() to handle duplicate emails gracefully
        user = User.objects.filter(email=email, role__in=['admin', 'owner']).first()
        
        if not user:
            # Don't reveal if email exists for security
            return Response(
                {'message': 'If that email is registered, a password reset link has been sent.'},
                status=status.HTTP_200_OK
            )
        
        # Create password reset token
        reset_token = PasswordResetToken.objects.create(user=user)
        
        # Build reset URL
        frontend_url = os.getenv('FRONTEND_URL', 'https://astucounselbot.vercel.app')
        reset_url = f"{frontend_url}/reset-password?token={reset_token.token}"
        
        # Send email using centralized function
        print(f"[ForgotPassword] Attempting to send reset email to: {user.email}")
        print(f"[ForgotPassword] Reset URL: {reset_url}")
        
        try:
            html_content = render_password_reset_email(user, reset_url)
            print(f"[ForgotPassword] Email template rendered successfully")
            
            subject = '🔐 Password Reset Request - Counselling Platform'
            text_body = f'Click this link to reset your password: {reset_url}\n\nThis link expires in 24 hours.'
            
            print(f"[ForgotPassword] Calling _send_email...")
            # Call _send_email from module level
            _send_email(subject, html_content, text_body, [user.email])
            
            print(f"[ForgotPassword] ✅ Password reset email sent to {user.email}")
        except Exception as e:
            print(f"[ForgotPassword] ❌ Failed to send password reset email: {e}")
            import traceback
            traceback.print_exc()
            # Still return success to not reveal email existence
        
        return Response(
            {'message': 'If that email is registered, a password reset link has been sent.'},
            status=status.HTTP_200_OK
        )


class ResetPasswordView(APIView):
    """
    POST /api/reset-password/
    Reset password using token
    Body: { "token": "uuid", "new_password": "newpass123" }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from .models import PasswordResetToken
        
        token_str = request.data.get('token', '').strip()
        new_password = request.data.get('new_password', '').strip()
        
        if not token_str or not new_password:
            return Response(
                {'error': 'Token and new password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find and validate token
        try:
            reset_token = PasswordResetToken.objects.get(token=token_str)
        except PasswordResetToken.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired reset token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not reset_token.is_valid():
            return Response(
                {'error': 'This reset link has expired or already been used'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset password FOR ALL USERS WITH THIS EMAIL
        user = reset_token.user
        print(f"[PasswordReset] ========================================")
        print(f"[PasswordReset] Resetting password for user: {user.username} (ID: {user.id})")
        print(f"[PasswordReset] User email: {user.email}")
        
        # Check for duplicate users with same email and update ALL of them
        from .models import User as UserModel
        users_with_email = UserModel.objects.filter(email=user.email)
        print(f"[PasswordReset] Users with email '{user.email}': {users_with_email.count()}")
        
        updated_count = 0
        for dup_user in users_with_email:
            print(f"[PasswordReset]   Updating password for ID: {dup_user.id}, Username: {dup_user.username}, Role: {dup_user.role}")
            dup_user.set_password(new_password)
            dup_user.save(update_fields=['password'])
            updated_count += 1
        
        # Force database commit
        from django.db import transaction
        transaction.commit()
        
        print(f"[PasswordReset] ✅ Updated password for {updated_count} user(s) with email {user.email}")
        
        # Mark token as used
        reset_token.used = True
        reset_token.save()
        
        # Verify by testing authentication with the original user
        from django.contrib.auth import authenticate
        auth_user = authenticate(username=user.username, password=new_password)
        if auth_user:
            print(f"[PasswordReset] ✅ Authentication test PASSED for user: {auth_user.username} (ID: {auth_user.id})")
        else:
            print(f"[PasswordReset] ⚠️ Authentication test failed for primary user")
        
        print(f"[PasswordReset] ✅ Password reset successful")
        print(f"[PasswordReset] ========================================")
        
        return Response(
            {'message': f'Password reset successful for all {updated_count} account(s) with this email. You can now login with any of your usernames.'},
            status=status.HTTP_200_OK
        )


# ─── Internal Message ViewSet ─────────────────────────────────────────────────

class InternalMessageViewSet(viewsets.ModelViewSet):
    queryset = InternalMessage.objects.all().order_by('-timestamp')
    serializer_class = InternalMessageSerializer
    permission_classes = [IsAdminOrOwner]

    def get_queryset(self):
        # Allow all admins and owners to see all internal messages
        queryset = InternalMessage.objects.all().order_by('timestamp')
        message_type = self.request.query_params.get('message_type')
        if message_type in ['chat', 'report']:
            queryset = queryset.filter(message_type=message_type)
        return queryset

    def perform_create(self, serializer):
        internal_message = serializer.save(sender=self.request.user)
        
        # Send email notification to other admins/owner
        try:
            send_internal_message_notification(internal_message, self.request.user)
        except Exception as e:
            print(f"[EMAIL NOTIFICATION] Error sending internal message notification: {e}")



# ─── Assignment Request ViewSet ───────────────────────────────────────────────

class AssignmentRequestViewSet(viewsets.ModelViewSet):
    """Handle assignment requests from admins"""
    from .models import AssignmentRequest
    from .serializers import AssignmentRequestSerializer
    
    queryset = AssignmentRequest.objects.all().order_by('-created_at')
    serializer_class = AssignmentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'owner':
            # Owner sees all requests
            return self.queryset
        elif user.role == 'admin':
            # Admin sees only their own requests
            return self.queryset.filter(admin=user)
        return self.queryset.none()

    def create(self, request):
        """Admin creates assignment request"""
        from .models import AssignmentRequest, Case
        
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admins can request assignments'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        case_id = request.data.get('case_id')
        if not case_id:
            return Response(
                {'error': 'case_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            case = Case.objects.get(id=case_id)
        except Case.DoesNotExist:
            return Response(
                {'error': 'Case not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if case is already assigned
        if case.status == 'assigned' and case.assigned_admin:
            return Response(
                {'error': 'Case is already assigned'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if admin already has pending request for this case
        existing_request = AssignmentRequest.objects.filter(
            case=case,
            admin=request.user,
            status='pending'
        ).first()
        
        if existing_request:
            return Response(
                {'error': 'You already have a pending request for this case'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the assignment request
        assignment_request = AssignmentRequest.objects.create(
            case=case,
            admin=request.user,
            status='pending'
        )
        
        serializer = self.serializer_class(assignment_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def approve(self, request, pk=None):
        """Owner approves assignment request"""
        from .models import Case
        from django.utils import timezone
        
        assignment_request = self.get_object()
        
        print(f"[APPROVE] Assignment request ID: {assignment_request.id}")
        print(f"[APPROVE] Current status: {assignment_request.status}")
        print(f"[APPROVE] Case ID: {assignment_request.case.id}")
        
        if assignment_request.status != 'pending':
            error_msg = f'Request has already been reviewed (current status: {assignment_request.status})'
            print(f"[APPROVE] ERROR: {error_msg}")
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Approve the request
        assignment_request.status = 'approved'
        assignment_request.reviewed_at = timezone.now()
        assignment_request.reviewed_by = request.user
        assignment_request.save()
        
        # Assign the case
        case = assignment_request.case
        case.assigned_admin = assignment_request.admin
        case.status = 'assigned'
        case.assigned_at = timezone.now()
        case.save()
        
        print(f"[APPROVE] ✅ Case assigned to {assignment_request.admin.username}")
        
        # Create audit log
        AuditLog.objects.create(
            case=case,
            performer=request.user,
            action='assigned',
            details=f'Approved assignment request - assigned case to admin {assignment_request.admin.username}',
        )
        
        # Notify user
        notify_case_user(case, f'Your case #{case.user_case_number} has been assigned to support.')
        
        serializer = self.serializer_class(assignment_request)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def reject(self, request, pk=None):
        """Owner rejects assignment request"""
        from django.utils import timezone
        
        assignment_request = self.get_object()
        
        if assignment_request.status != 'pending':
            return Response(
                {'error': 'Request has already been reviewed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reject the request
        assignment_request.status = 'rejected'
        assignment_request.reviewed_at = timezone.now()
        assignment_request.reviewed_by = request.user
        assignment_request.save()
        
        serializer = self.serializer_class(assignment_request)
        return Response(serializer.data)


# ─── Feedback ViewSet ─────────────────────────────────────────────────────────

class FeedbackViewSet(viewsets.ModelViewSet):
    """Feedback management - users can create, staff can view"""
    from .models import Feedback
    from .serializers import FeedbackSerializer
    
    queryset = Feedback.objects.all().order_by('-created_at')
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'owner':
            # Owner sees all feedback
            return self.queryset
        elif user.role == 'admin':
            # Admin sees feedback only for cases assigned to them
            return self.queryset.filter(case__assigned_admin=user)
        elif user.role == 'user':
            # Users see their own feedback
            return self.queryset.filter(user=user)
        return self.queryset.none()
    
    def create(self, request):
        """Create feedback for a closed case"""
        from .models import Case, Feedback
        
        case_id = request.data.get('case')
        content = request.data.get('content', '').strip()
        rating = request.data.get('rating')
        
        if not case_id or not content:
            return Response(
                {'error': 'case and content are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            case = Case.objects.get(id=case_id)
        except Case.DoesNotExist:
            return Response(
                {'error': 'Case not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Only the case owner can leave feedback
        if request.user != case.user:
            return Response(
                {'error': 'You can only leave feedback on your own cases'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if case is closed
        if case.status != 'closed':
            return Response(
                {'error': 'Feedback can only be provided for closed cases'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if feedback already exists
        if hasattr(case, 'feedback'):
            return Response(
                {'error': 'Feedback already submitted for this case'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create feedback
        feedback = Feedback.objects.create(
            case=case,
            user=request.user,
            content=content,
            rating=rating if rating else None
        )
        
        serializer = self.serializer_class(feedback)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─── Analytics ViewSet ────────────────────────────────────────────────────────

class AnalyticsViewSet(viewsets.ViewSet):
    """Analytics and reports for admins and owners"""
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """Get analytics dashboard data"""
        from .models import Case, Feedback
        from django.db.models import Count, Avg, Q
        from django.utils import timezone
        from datetime import timedelta
        
        user = request.user
        
        if user.role not in ['admin', 'owner']:
            return Response(
                {'error': 'Only admins and owners can access analytics'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Filter cases based on role
        if user.role == 'owner':
            cases = Case.objects.all()
        else:
            cases = Case.objects.filter(assigned_admin=user)
        
        # Total cases by status
        total_cases = cases.count()
        open_cases = cases.filter(status='open').count()
        assigned_cases = cases.filter(status='assigned').count()
        resolved_cases = cases.filter(status='resolved').count()
        closed_cases = cases.filter(status='closed').count()
        
        # Cases per admin (owner only)
        cases_per_admin = []
        if user.role == 'owner':
            from .models import User
            admins = User.objects.filter(role='admin')
            for admin in admins:
                admin_cases = Case.objects.filter(assigned_admin=admin)
                cases_per_admin.append({
                    'admin_name': admin.username,
                    'total': admin_cases.count(),
                    'open': admin_cases.filter(status='open').count(),
                    'assigned': admin_cases.filter(status='assigned').count(),
                    'resolved': admin_cases.filter(status='resolved').count(),
                    'closed': admin_cases.filter(status='closed').count(),
                })
        
        # Average resolution time (for closed cases with timestamps)
        closed_with_times = cases.filter(
            status='closed',
            assigned_at__isnull=False,
            closed_at__isnull=False
        )
        
        avg_resolution_seconds = None
        avg_resolution_hours = None
        if closed_with_times.exists():
            total_seconds = sum([
                (case.closed_at - case.assigned_at).total_seconds()
                for case in closed_with_times
            ])
            avg_resolution_seconds = total_seconds / closed_with_times.count()
            avg_resolution_hours = round(avg_resolution_seconds / 3600, 2)
        
        # Cases per day/week/month
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)
        today = now.date()
        
        cases_today = cases.filter(created_at__date=today).count()
        cases_last_7_days = cases.filter(created_at__gte=last_7_days).count()
        cases_last_30_days = cases.filter(created_at__gte=last_30_days).count()
        
        # Daily cases for last 30 days (for charts)
        daily_cases = []
        for i in range(30):
            day = (now - timedelta(days=i)).date()
            count = cases.filter(created_at__date=day).count()
            daily_cases.append({
                'date': day.isoformat(),
                'count': count
            })
        daily_cases.reverse()
        
        # User satisfaction from feedback ratings
        feedbacks = Feedback.objects.filter(case__in=cases, rating__isnull=False)
        avg_rating = feedbacks.aggregate(Avg('rating'))['rating__avg']
        total_feedbacks = feedbacks.count()
        
        # Rating distribution
        rating_distribution = []
        for rating in range(1, 6):
            count = feedbacks.filter(rating=rating).count()
            rating_distribution.append({
                'rating': rating,
                'count': count
            })
        
        return Response({
            'total_cases': total_cases,
            'cases_by_status': {
                'open': open_cases,
                'assigned': assigned_cases,
                'resolved': resolved_cases,
                'closed': closed_cases,
            },
            'cases_per_admin': cases_per_admin,
            'resolution_time': {
                'average_hours': avg_resolution_hours,
                'total_closed_cases': closed_with_times.count(),
            },
            'cases_timeline': {
                'today': cases_today,
                'last_7_days': cases_last_7_days,
                'last_30_days': cases_last_30_days,
                'daily': daily_cases,
            },
            'user_satisfaction': {
                'average_rating': round(avg_rating, 2) if avg_rating else None,
                'total_feedbacks': total_feedbacks,
                'rating_distribution': rating_distribution,
            }
        })
