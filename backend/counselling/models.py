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
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Case {self.id}: {self.title}"

class Message(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
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
