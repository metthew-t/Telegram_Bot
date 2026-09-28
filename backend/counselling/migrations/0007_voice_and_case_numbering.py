# Generated migration for voice messages and per-user case numbering

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0006_user_email_verification_token_user_email_verified'),
    ]

    operations = [
        # Add voice fields to Message model
        migrations.AddField(
            model_name='message',
            name='message_type',
            field=models.CharField(
                choices=[('text', 'Text'), ('voice', 'Voice')],
                default='text',
                max_length=10
            ),
        ),
        migrations.AddField(
            model_name='message',
            name='voice_data',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='voice_duration',
            field=models.IntegerField(blank=True, null=True),
        ),
        
        # Add voice and format fields to InternalMessage model
        migrations.AddField(
            model_name='internalmessage',
            name='message_format',
            field=models.CharField(
                choices=[('text', 'Text'), ('voice', 'Voice'), ('file', 'File')],
                default='text',
                max_length=10
            ),
        ),
        migrations.AddField(
            model_name='internalmessage',
            name='voice_data',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='internalmessage',
            name='voice_duration',
            field=models.IntegerField(blank=True, null=True),
        ),
        
        # Add per-user case numbering to Case model
        migrations.AddField(
            model_name='case',
            name='user_case_number',
            field=models.IntegerField(default=1),
        ),
        
        # Add ordering to Case model
        migrations.AlterModelOptions(
            name='case',
            options={'ordering': ['-created_at']},
        ),
    ]
