# Generated migration for CaseAssignmentRequest model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0013_internalchatview_caseview'),
    ]

    operations = [
        migrations.CreateModel(
            name='CaseAssignmentRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
                    default='pending',
                    max_length=20
                )),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('case', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='assignment_requests_v2',
                    to='counselling.case'
                )),
                ('requesting_admin', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='my_assignment_requests',
                    to=settings.AUTH_USER_MODEL
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_assignment_requests',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'ordering': ['-requested_at'],
            },
        ),
    ]
