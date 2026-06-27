import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User
from django.contrib.auth import authenticate

u = User.objects.get(username='owner')
print(f"User: {u.username}")
print(f"Email verified: {u.email_verified} (type: {type(u.email_verified)})")

auth_u = authenticate(username='owner', password='owner1234')
if auth_u:
    print(f"Auth success! Verified: {auth_u.email_verified}")
else:
    print("Auth failed!")
