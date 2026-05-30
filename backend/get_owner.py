import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from counselling.models import User

owner = User.objects.filter(role='owner').first()
if not owner:
    owner = User.objects.create_superuser(username='admin_owner', email='owner@example.com', password='password123')
    owner.role = 'owner'
    owner.save()
    print(f"Created new owner: {owner.username} / password123")
else:
    owner.set_password('password123')
    owner.save()
    print(f"Updated owner: {owner.username} / password123")
