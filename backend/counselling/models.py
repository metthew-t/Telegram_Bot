import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
        ('owner', 'Owner'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    telegram_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.username} ({self.role})"

class Case(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('closed', 'Closed'),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cases')
    assigned_admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_cases')
    user_case_number = models.IntegerField(default=1)  # Per-user case numbering
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Auto-assign user_case_number if this is a new case
        if not self.pk:  # New case
            last_case = Case.objects.filter(user=self.user).order_by('-user_case_number').first()
            if last_case:
                self.user_case_number = last_case.user_case_number + 1
            else:
                self.user_case_number = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Case {self.id}: {self.title}"

class Message(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('voice', 'Voice'),
    ]
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    voice_data = models.TextField(null=True, blank=True)  # Base64 encoded audio
    voice_duration = models.IntegerField(null=True, blank=True)  # Duration in seconds
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Message from {self.sender} in {self.case}"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('assigned', 'Assigned'),
        ('reassigned', 'Reassigned'),
        ('closed', 'Closed'),
        ('reply', 'Reply'),
        ('submitted', 'Submitted'),
    ]
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='audit_logs')
    performer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.action} for case {self.case.id} by {self.performer or 'system'}"
class InternalMessage(models.Model):
    TYPE_CHOICES = [
        ('chat', 'Chat'),
        ('report', 'Report'),
    ]
    MESSAGE_FORMAT_CHOICES = [
        ('text', 'Text'),
        ('voice', 'Voice'),
        ('file', 'File'),
    ]
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='internal_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='chat')
    message_format = models.CharField(max_length=10, choices=MESSAGE_FORMAT_CHOICES, default='text')
    voice_data = models.TextField(null=True, blank=True)  # Base64 encoded audio
    voice_duration = models.IntegerField(null=True, blank=True)  # Duration in seconds
    timestamp = models.DateTimeField(default=timezone.now)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_content = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Internal {self.message_type} from {self.sender} at {self.timestamp}"
