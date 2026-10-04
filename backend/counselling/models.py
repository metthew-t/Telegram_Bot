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
    email_notifications_enabled = models.BooleanField(default=True)  # Allow admins to toggle notifications
    email_approved_by_owner = models.BooleanField(default=False)  # Owner must approve admin emails for notifications
    profile_photo = models.TextField(null=True, blank=True)  # Base64 encoded image

    def __str__(self):
        return f"{self.username} ({self.role})"

class Case(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('resolved', 'Resolved'),
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
    assigned_at = models.DateTimeField(null=True, blank=True)  # Time when case was assigned
    resolved_at = models.DateTimeField(null=True, blank=True)  # Time when case was resolved
    closed_at = models.DateTimeField(null=True, blank=True)  # Time when case was closed

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


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Set expiration to 24 hours from creation
        if not self.pk:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if token is still valid (not expired and not used)"""
        return not self.used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Password reset for {self.user.username} - {'Valid' if self.is_valid() else 'Invalid'}"


class AssignmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='assignment_requests')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_assignment_requests')

    def __str__(self):
        return f"Assignment request for case {self.case.id} by {self.admin.username} - {self.status}"


class Feedback(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name='feedback')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    content = models.TextField()
    rating = models.IntegerField(null=True, blank=True)  # Optional rating 1-5
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Feedback for case {self.case.id} from {self.user.username}"
