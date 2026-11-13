# Generated migration for Message and InternalMessage edit fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0016_message_seen_by_user_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_edited',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='message',
            name='edited_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='internalmessage',
            name='is_edited',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='internalmessage',
            name='edited_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
