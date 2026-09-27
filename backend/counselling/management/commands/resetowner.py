"""
Django management command to reset owner password and verify email
Usage: python manage.py resetowner
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Reset owner password to owner1234 and verify email'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n🔧 Resetting owner account...\n'))
        
        # Find or create owner
        owner = User.objects.filter(username='owner').first()
        
        if not owner:
            self.stdout.write(self.style.WARNING('⚠️  Owner not found. Creating new owner...'))
            owner = User.objects.create(
                username='owner',
                email='owner@example.com',
                role='owner'
            )
        
        # Reset password and verify email
        owner.set_password('owner1234')
        owner.email_verified = True
        owner.save()
        
        self.stdout.write(self.style.SUCCESS('✅ Owner account ready!'))
        self.stdout.write(self.style.SUCCESS(f'   Username: {owner.username}'))
        self.stdout.write(self.style.SUCCESS(f'   Password: owner1234'))
        self.stdout.write(self.style.SUCCESS(f'   Email: {owner.email}'))
        self.stdout.write(self.style.SUCCESS(f'   Email verified: {owner.email_verified}'))
        self.stdout.write(self.style.SUCCESS(f'   Role: {owner.role}\n'))
