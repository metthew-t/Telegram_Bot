# Generated manually - Change Case.user from CASCADE to SET_NULL

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('counselling', '0010_add_assignment_feedback_timetracking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cases', to=settings.AUTH_USER_MODEL),
        ),
    ]
