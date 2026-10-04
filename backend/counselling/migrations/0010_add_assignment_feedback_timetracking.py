# Generated migration for assignment requests, feedback, and time tracking

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0009_user_profile_photo'),
    ]

    operations = [
        # Add time tracking fields to Case model
        migrations.AddField(
            model_name='case',
            name='assigned_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='resolved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='case',
            name='closed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        
        # Update Case status choices to include 'resolved'
        migrations.AlterField(
            model_name='case',
            name='status',
            field=models.CharField(
                choices=[
                    ('open', 'Open'),
                    ('assigned', 'Assigned'),
                    ('resolved', 'Resolved'),
                    ('closed', 'Closed')
                ],
                default='open',
                max_length=10
            ),
        ),
        
        # Create AssignmentRequest model
        migrations.CreateModel(
            name='AssignmentRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Pending'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected')
                    ],
                    default='pending',
                    max_length=10
                )),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('admin', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignment_requests',
                    to=settings.AUTH_USER_MODEL
                )),
                ('case', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignment_requests',
                    to='counselling.case'
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_assignment_requests',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
        ),
        
        # Create Feedback model
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('rating', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('case', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='feedback',
                    to='counselling.case'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='feedbacks',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
        ),
    ]
