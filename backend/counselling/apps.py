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
                owner.save()
                print("Reset existing owner password to: owner1234")
            else:
                u = User(username='owner', email='owner@example.com', role='owner')
                u.set_password('owner1234')
                u.save()
                print("Created default owner account: owner / owner1234")
        except Exception as e:
            pass
