import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'counselling_platform.settings')
django.setup()

from counselling.models import User

try:
    owner = User.objects.get(username='owner')
    owner.email = 'metthewsteferi@gmail.com'
    owner.email_verified = True
    owner.save(update_fields=['email', 'email_verified'])
    print(f"Successfully updated owner email to {owner.email} and set as verified!")
except User.DoesNotExist:
    print("Error: User with username 'owner' does not exist.")
except Exception as e:
    print(f"An error occurred: {e}")
