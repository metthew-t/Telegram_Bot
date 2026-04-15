from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserViewSet,
    CaseViewSet,
    MessageViewSet,
    AuditLogViewSet,
    LoginView,
    ProfileView,
    TelegramLoginView,
    InternalMessageViewSet,
    api_root,
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'cases', CaseViewSet)
router.register(r'messages', MessageViewSet)
router.register(r'audit-logs', AuditLogViewSet)
router.register(r'internal-messages', InternalMessageViewSet)

urlpatterns = [
    path('', api_root, name='index'),
    path('api/', include(router.urls)),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/telegram-login/', TelegramLoginView.as_view(), name='telegram_login'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/profile/', ProfileView.as_view(), name='profile'),
]