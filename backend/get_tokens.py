import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User

unverified_users = User.objects.filter(email_verified=False).exclude(email_verification_token__isnull=True)

print("\n" + "="*60)
print("UNVERIFIED USERS AND THEIR VERIFICATION LINKS:")
print("="*60)

for user in unverified_users:
    token = user.email_verification_token
    link = f"http://localhost:8000/api/verify-email/?token={token}"
    print(f"Username: {user.username}\nEmail: {user.email}\nLink: {link}\n" + "-"*30)

print("="*60 + "\n")
