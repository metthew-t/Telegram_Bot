from django.contrib import admin
from .models import User, Case, Message

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'telegram_id']

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
