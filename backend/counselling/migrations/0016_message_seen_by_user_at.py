# Generated migration for Message.seen_by_user_at field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0015_message_seen_by_admin_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='seen_by_user_at',
            field=models.DateTimeField(blank=True, null=True, help_text='When user viewed this admin message'),
        ),
    ]
