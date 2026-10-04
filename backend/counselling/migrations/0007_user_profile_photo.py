# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0006_user_email_verification_token_user_email_verified'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_photo',
            field=models.TextField(blank=True, null=True),
        ),
    ]
