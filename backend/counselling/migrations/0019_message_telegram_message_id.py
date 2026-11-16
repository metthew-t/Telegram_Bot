from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0018_case_busy_notice_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='telegram_message_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]

