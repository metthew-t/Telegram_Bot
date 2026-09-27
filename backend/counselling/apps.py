from django.apps import AppConfig
import sys

class CounsellingConfig(AppConfig):
    name = "counselling"

    def ready(self):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            owner = User.objects.filter(role='owner').first()
            if owner:
                owner.set_password('owner1234')
                owner.email_verified = True  # Ensure owner can always login
                owner.save()
                print("✅ Reset existing owner password to: owner1234 (email verified)")
            else:
                u = User(username='owner', email='owner@example.com', role='owner')
                u.set_password('owner1234')
                u.email_verified = True  # Ensure owner can always login
                u.save()
                print("✅ Created default owner account: owner / owner1234 (email verified)")
        except Exception as e:
            pass
