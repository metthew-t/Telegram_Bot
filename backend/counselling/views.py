import os
import requests

from django.db.models import Q
from django.contrib.auth import authenticate
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Case, Message, AuditLog
from .serializers import UserSerializer, CaseSerializer, MessageSerializer, AuditLogSerializer


def notify_case_user(case, text):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("Backend Error: TELEGRAM_BOT_TOKEN not set in environment.")
        return
        
    if not case.user.telegram_id:
        print(f"Backend Warning: Case #{case.id} user has no telegram_id.")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": case.user.telegram_id,
        "text": text,
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Telegram API Error: {response.status_code} - {response.text}")
        else:
            print(f"Notification sent successfully to telegram_id {case.user.telegram_id}")
    except Exception as e:
        print(f"Telegram Notification Exception: {str(e)}")


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
        # Admin self-registration defaults to 'admin'
        # Owner can create any role (including owner)
        if self.request.user.is_authenticated and self.request.user.role == 'owner':
            serializer.save()
        else:
            serializer.save(role='admin')

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
            serializer.save(user=self.request.user)

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
            return Response({'status': 'closed'})
        raise PermissionDenied('Permission denied')

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
        if user.role in ['admin', 'owner'] and case.user.telegram_id:
            notify_case_user(case, f'New response on case #{case.id}: {message.content}')
        AuditLog.objects.create(
            case=case,
            performer=user,
            action='reply' if user.role in ['admin', 'owner'] else 'submitted',
            details=f'Message created by {user.username}: {message.content[:120]}',
        )

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-created_at')
    serializer_class = AuditLogSerializer
    permission_classes = [IsOwner]

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
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
