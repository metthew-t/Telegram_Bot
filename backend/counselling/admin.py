from django.contrib import admin
from .models import User, Case, Message, AuditLog, PasswordResetToken, CaseView, InternalChatView

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'telegram_id', 'email_verified', 'email_approved_by_owner']

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'status', 'user', 'assigned_admin', 'created_at']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'case', 'sender', 'timestamp']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'case', 'performer', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['case__id', 'performer__username', 'details']

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'used']
    list_filter = ['used', 'created_at']
    search_fields = ['user__username', 'token']

@admin.register(CaseView)
class CaseViewAdmin(admin.ModelAdmin):
    list_display = ['case', 'user', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['case__id', 'user__username']

@admin.register(InternalChatView)
class InternalChatViewAdmin(admin.ModelAdmin):
    list_display = ['user', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__username']
