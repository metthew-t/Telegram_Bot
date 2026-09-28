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


# ─── Root ────────────────────────────────────────────────────────────────────

def api_root(request):
    return JsonResponse({
        "status": "online",
        "message": "Counselling Platform API is running",
        "endpoints": {
            "api": "/api/",
            "admin": "/admin/",
        }
    })


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

    @action(detail=True, methods=['post'], permission_classes=[IsOwner])
    def verify(self, request, pk=None):
        """Owner can manually mark an admin/user as email-verified (useful when email delivery fails)."""
        user = self.get_object()
        user.email_verified = True
        user.email_verification_token = None
        user.save(update_fields=['email_verified', 'email_verification_token'])
        return Response({'status': 'verified', 'username': user.username})

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
            return Case.objects.filter(Q(assigned_admin=user) | Q(status='open'))
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
                send_email_to_staff(subject, html_body, text_body)
            except Exception as exc:
                print(f"[Email] New-case email failed: {exc}")

    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrOwner])
    def assign(self, request, pk=None):
        case = self.get_object()
        admin_id = request.data.get('admin_id')
        try:
            admin = User.objects.get(id=admin_id, role='admin')
        except User.DoesNotExist:
            return Response({'error': 'Admin not found'}, status=status.HTTP_400_BAD_REQUEST)

        case.assigned_admin = admin
        case.status = 'assigned'
        case.save()
        AuditLog.objects.create(
            case=case,
            performer=request.user,
            action='assigned',
            details=f'Assigned case to admin {admin.username}',
        )
        notify_case_user(case, f'Your case #{case.id} has been assigned to support.')

        frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')

        # ── Email: notify the assigned admin + owners ──
        try:
            subject, html_body, text_body = render_case_assigned_email(
                case, admin.username, request.user.username, frontend_url
            )
            # Collect verified emails: assigned admin + all owners
            recipients = []
            if admin.email and admin.email_verified:
                recipients.append(admin.email)
            owner_emails = _owner_email_recipients()
            recipients.extend(e for e in owner_emails if e not in recipients)
            if recipients:
                _send_email(subject, html_body, text_body, recipients)
        except Exception as exc:
            print(f"[Email] Case-assigned email failed: {exc}")

        return Response({'status': 'assigned'})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        case = self.get_object()
        if request.user.role == 'owner' or (request.user.role == 'admin' and case.assigned_admin == request.user) or case.user == request.user:
            case.status = 'closed'
            case.save()
            AuditLog.objects.create(
                case=case,
                performer=request.user,
                action='closed',
                details=f'Case closed by {request.user.username}',
            )
            notify_case_user(case, f'Your case #{case.id} has been closed.')

            frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173')).rstrip('/')

            # ── Email ──
            try:
                subject, html_body, text_body = render_case_closed_email(case, request.user.username, frontend_url)
                send_email_to_staff(subject, html_body, text_body)
            except Exception as exc:
                print(f"[Email] Case-closed email failed: {exc}")

            return Response({'status': 'closed'})
        raise PermissionDenied('Permission denied')


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
        
        allowed = (
            user.role == 'owner' or
            user.role == 'admin' or   # Any admin can reply to any case they can view
            case.user == user
        )
        
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
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


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
        serializer.save(sender=self.request.user)


# ─── Telegram Diagnostic View (temporary debug) ──────────────────────────────

class TelegramDiagnosticView(APIView):
    """Temporary diagnostic endpoint to debug Telegram notifications on Render."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        import requests as req

        token = os.getenv('TELEGRAM_BOT_TOKEN')
        results = {
            'telegram_bot_token_set': bool(token),
            'telegram_bot_token_preview': f"{token[:15]}...{token[-6:]}" if token else None,
        }

        # Check all users with telegram_id
        users_with_telegram = list(
            User.objects.exclude(telegram_id__isnull=True)
            .exclude(telegram_id='')
            .values('id', 'username', 'telegram_id', 'role')
        )
        results['users_with_telegram_id'] = users_with_telegram

        # Check all cases and their user's telegram_id
        cases_info = []
        for case in Case.objects.all().select_related('user')[:20]:
            cases_info.append({
                'case_id': case.id,
                'title': case.title,
                'case_user': case.user.username,
                'case_user_telegram_id': case.user.telegram_id,
                'status': case.status,
            })
        results['cases'] = cases_info

        # Test sending a message if telegram_id provided
        test_tid = request.query_params.get('test_telegram_id')
        if test_tid and token:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {"chat_id": str(test_tid).strip(), "text": "Diagnostic test from Render backend"}
            try:
                resp = req.post(url, json=payload, timeout=10)
                results['test_send'] = {
                    'telegram_id_tested': test_tid,
                    'http_status': resp.status_code,
                    'response': resp.json(),
                }
            except Exception as e:
                results['test_send'] = {'error': str(e)}

        return Response(results)
