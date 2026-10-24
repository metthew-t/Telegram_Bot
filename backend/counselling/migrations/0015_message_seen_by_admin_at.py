# Generated migration for Message.seen_by_admin_at field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0014_caseassignmentrequest'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='seen_by_admin_at',
            field=models.DateTimeField(blank=True, null=True, help_text='When admin viewed this message'),
        ),
    ]
