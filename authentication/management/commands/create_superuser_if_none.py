from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create a superuser if none exists'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Check if any superuser exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.SUCCESS('✅ Superuser already exists')
            )
            return
        
        # Get credentials from environment or use defaults
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@carental.com')
        full_name = os.environ.get('DJANGO_SUPERUSER_FULL_NAME', 'Admin User')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'AdminPass123!')
        
        # Create superuser using your CustomUser model
        try:
            User.objects.create_superuser(
                email=email,
                full_name=full_name,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Superuser "{email}" created successfully!')
            )
            self.stdout.write(
                self.style.WARNING(f'🔑 Login credentials: {email} / {password}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create superuser: {e}')
            )