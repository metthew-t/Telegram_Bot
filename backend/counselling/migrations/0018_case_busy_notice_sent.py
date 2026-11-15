# Generated migration for Case busy_notice_sent and AuditLog busy_notice choice

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0017_message_edited_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='case',
            name='busy_notice_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('assigned', 'Assigned'),
                    ('reassigned', 'Reassigned'),
                    ('closed', 'Closed'),
                    ('reply', 'Reply'),
                    ('submitted', 'Submitted'),
                    ('busy_notice', 'Counselors Busy Notice'),
                ],
                max_length=50
            ),
        ),
    ]

