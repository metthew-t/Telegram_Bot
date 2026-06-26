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
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("Backend Error: TELEGRAM_BOT_TOKEN not set in environment.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Telegram API Error: {response.status_code} - {response.text}")
            return False
        return True
    except Exception as e:
        print(f"Telegram Notification Exception: {str(e)}")
        return False


def notify_case_user(case, text):
    if not case.user.telegram_id:
        print(f"Backend Warning: Case #{case.id} user has no telegram_id.")
        return
    send_telegram_notification(case.user.telegram_id, text)


def notify_staff(text):
    staff_users = User.objects.filter(role__in=['admin', 'owner']).exclude(telegram_id__isnull=True).exclude(telegram_id='')
    for user in staff_users:
        send_telegram_notification(user.telegram_id, text)


# ─── Email Notification Helpers ──────────────────────────────────────────────

def _send_email(subject: str, html_body: str, text_body: str, recipients: list):
    """Send a multipart (HTML + plain text) email to a list of recipients via SendGrid API."""
    if not recipients:
        return
        
    api_key = os.getenv('BREVO_API_KEY')
    if not api_key:
        print(f"\n[Brevo Skipped] BREVO_API_KEY not found. Email to {recipients} not sent.")
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
            print(f"[Email] Sent '{subject}' to {len(recipients)} recipient(s) via Brevo.")
        else:
            print(f"[Email] Brevo API Error {response.status_code}: {response.text}")
    except Exception as exc:
        print(f"[Email] Failed to send '{subject}': {exc}")


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


def send_verification_email(user, request):
    """Generate a UUID token, save it, and dispatch the formal verification email."""
    token = uuid.uuid4()
    user.email_verification_token = token
    user.email_verified = False
    user.save(update_fields=['email_verification_token', 'email_verified'])

    backend_url = getattr(settings, 'BACKEND_URL', os.getenv('BACKEND_URL', 'http://localhost:8000'))
    frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173'))
    verification_link = f"{backend_url}/api/verify-email/?token={token}"

    print(f"\n\n{'='*60}\n[ACTION REQUIRED] VERIFICATION LINK FOR {user.username}:\n{verification_link}\n{'='*60}\n\n")

    subject, html_body, text_body = render_verification_email(user, verification_link)
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

        frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173'))
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
            frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173'))

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

        frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173'))

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

            frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173'))

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
            queryset = queryset.filter(case__assigned_admin=user)
        else:
            queryset = queryset.filter(case__user=user)
        if case_id:
            queryset = queryset.filter(case_id=case_id)
        return queryset

    def perform_create(self, serializer):
        case = serializer.validated_data['case']
        user = self.request.user
        allowed = (
            user.role == 'owner' or
            (user.role == 'admin' and case.assigned_admin == user) or
            case.user == user
        )
        if not allowed:
            raise PermissionDenied('Permission denied')

        message = serializer.save(sender=user)
        frontend_url = getattr(settings, 'FRONTEND_URL', os.getenv('FRONTEND_URL', 'http://localhost:5173'))

        if user.role in ['admin', 'owner']:
            # Notify case user via Telegram
            if case.user.telegram_id:
                notify_case_user(case, f'💬 *New support response on case #{case.id}:*\n\n{message.content}')

            # Email owners for oversight (admin replied)
            try:
                subject, html_body, text_body = render_new_message_email(
                    case, message, user.username, frontend_url
                )
                send_email_to_owners(subject, html_body, text_body)
            except Exception as exc:
                print(f"[Email] Admin-reply email failed: {exc}")
        else:
            # Client replied — notify all staff
            notify_staff(
                f"💬 *New message on case #{case.id}*\n"
                f"👤 From: {user.username}\n\n"
                f"{message.content}"
            )

            # Email all verified staff
            try:
                subject, html_body, text_body = render_new_message_email(
                    case, message, user.username, frontend_url
                )
                send_email_to_staff(subject, html_body, text_body)
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
            if user.role in ['admin', 'owner'] and not user.email_verified:
                if user.email:
                    try:
                        send_verification_email(user, request)
                    except Exception as exc:
                        print(f"[Email] Resend verification email failed for {user.username}: {exc}")
                return Response({'error': 'Please verify your email address before logging in. A new verification link has been sent to your email!'}, status=status.HTTP_403_FORBIDDEN)
                
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
