# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0008_user_email_approved_by_owner_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_photo',
            field=models.TextField(blank=True, null=True),
        ),
    ]
