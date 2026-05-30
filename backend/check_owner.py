import os
import sys
import django

# Must run from the backend/ directory
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
os.environ.setdefault('USE_SQLITE', '1')

django.setup()

from counselling.models import User

owner = User.objects.filter(role='owner').first()
if owner:
    # Reset password to known value
    owner.set_password('owner1234')
    owner.save()
    print(f"Owner found: {owner.username} | Password reset to: owner1234")
else:
    # Create a fresh owner
    u = User(username='owner', role='owner')
    u.set_password('owner1234')
    u.save()
    print(f"Created new owner: owner | Password: owner1234")
