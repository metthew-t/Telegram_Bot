"""
Django management command to ensure owner account exists
Usage: python manage.py resetowner
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Ensure owner account exists (does NOT reset password if owner already exists)'

    def handle(self, *args, **options):
        # Find existing owner
        owner = User.objects.filter(role='owner').first()
        
        if owner:
            # Owner already exists — do NOT touch the password
            # Only ensure email_verified is True so they can always log in
            if not owner.email_verified:
                owner.email_verified = True
                owner.save()
                self.stdout.write(self.style.SUCCESS(f'✅ Owner "{owner.username}" email_verified set to True'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✅ Owner "{owner.username}" already exists (password unchanged)'))
        else:
            # No owner exists — create one with default credentials
            owner = User.objects.create(
                username='owner',
                email='owner@example.com',
                role='owner'
            )
            owner.set_password('owner1234')
            owner.email_verified = True
            owner.save()
            self.stdout.write(self.style.SUCCESS('✅ Created new owner: owner / owner1234'))

