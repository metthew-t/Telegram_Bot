import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User

if len(sys.argv) < 2:
    print("Usage: python verify_user.py <username>")
    sys.exit(1)

username = sys.argv[1]

try:
    user = User.objects.get(username=username)
    user.email_verified = True
    user.save(update_fields=['email_verified'])
    print(f"Success! '{username}' has been successfully verified and can now log in.")
except User.DoesNotExist:
    print(f"Error: User '{username}' does not exist.")
