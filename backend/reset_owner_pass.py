import os
import sys

# Set environment variables BEFORE importing Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'counselling_platform.settings'
os.environ['USE_SQLITE'] = '1'
# Prevent dj_database_url from failing by providing a dummy DATABASE_URL for SQLite
os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'

import django
django.setup()

from counselling.models import User

owners = User.objects.filter(role='owner')
print(f"Found {owners.count()} owner(s):")
for o in owners:
    o.set_password('Admin@1234')
    o.save()
    print(f"  Username: {o.username} | Password reset to: Admin@1234")
