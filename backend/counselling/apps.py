from django.apps import AppConfig
import sys

class CounsellingConfig(AppConfig):
    name = "counselling"

    def ready(self):
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Only create if tables exist and no owner is found
            if not User.objects.filter(role='owner').exists():
                u = User(username='owner', email='owner@example.com', role='owner')
                u.set_password('owner1234')
                u.save()
                print("Created default owner account: owner / owner1234")
        except Exception:
            # Silently ignore if tables don't exist yet (e.g. during migrations)
            pass
