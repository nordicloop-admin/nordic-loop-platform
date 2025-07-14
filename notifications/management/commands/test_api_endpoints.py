from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class Command(BaseCommand):
    help = 'Tests the notifications API endpoints directly'

    def handle(self, *args, **options):
        # Get an admin user
        try:
            admin_user = User.objects.filter(is_staff=True).first() or User.objects.filter(role='Admin').first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('No admin user found. Please create one first.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error finding admin user: {e}'))
            return
            
        # Get a regular user
        try:
            regular_user = User.objects.filter(is_staff=False, is_superuser=False).exclude(id=admin_user.id).first()
            if not regular_user:
                self.stdout.write(self.style.ERROR('No regular user found. Please create one first.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error finding regular user: {e}'))
            return
            
        self.stdout.write(self.style.SUCCESS(f'Using admin user: {admin_user.username}'))
        self.stdout.write(self.style.SUCCESS(f'Using regular user: {regular_user.username}'))
        
        # Get tokens for authentication
        admin_token = str(RefreshToken.for_user(admin_user).access_token)
        user_token = str(RefreshToken.for_user(regular_user).access_token)
        
        # Create API clients
        admin_client = APIClient()
        admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        
        user_client = APIClient()
        user_client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')
        
        # Test endpoints
        self.test_list_notifications(user_client, 'Regular user')
        self.test_list_unread(user_client, 'Regular user')
        self.test_list_all(admin_client, 'Admin')
        
    def test_list_notifications(self, client, user_type):
        self.stdout.write(f'\n{user_type} - List notifications:')
        response = client.get('/api/notifications/')
        self.print_response(response)
        
    def test_list_unread(self, client, user_type):
        self.stdout.write(f'\n{user_type} - List unread notifications:')
        response = client.get('/api/notifications/unread/')
        self.print_response(response)
        
    def test_list_all(self, client, user_type):
        self.stdout.write(f'\n{user_type} - List all notifications (admin):')
        response = client.get('/api/notifications/list-all/')
        self.print_response(response)
        
    def print_response(self, response):
        self.stdout.write(f'Status code: {response.status_code}')
        if response.status_code == 200:
            try:
                self.stdout.write(f'Response data: {response.data}')
                self.stdout.write(f'Count: {len(response.data)}')
            except AttributeError:
                self.stdout.write(f'Response content: {response.content}')
        else:
            self.stdout.write(f'Response content: {response.content}')
