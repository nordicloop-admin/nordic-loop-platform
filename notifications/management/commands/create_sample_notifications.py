from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from notifications.models import Notification
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample notifications in the database'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of notifications to create')
        parser.add_argument('--broadcast', action='store_true', help='Create broadcast notifications (no specific user)')

    def handle(self, *args, **options):
        count = options['count']
        broadcast = options['broadcast']
        
        # Get all users or create a test user if none exists
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found. Creating a test user...'))
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='testpassword123',
                is_staff=True
            )
            users = User.objects.all()
        
        notification_types = ['info', 'success', 'warning', 'error', 'system']
        sample_titles = [
            'New Feature Available',
            'Your Ad Has Been Approved',
            'Bid Received on Your Ad',
            'Account Update Required',
            'Welcome to Nordic Loop',
            'Maintenance Scheduled',
            'Password Reset Requested',
            'New Message Received',
            'Payment Processed Successfully',
            'Action Required: Verify Your Email'
        ]
        
        sample_messages = [
            'We have added a new feature to help you manage your ads more efficiently.',
            'Your ad has been reviewed and approved by our team. It is now visible to potential buyers.',
            'Someone has placed a bid on your item. Check your dashboard for details.',
            'Please update your account information to ensure uninterrupted service.',
            'Welcome to Nordic Loop! We are excited to have you join our community.',
            'The system will be down for maintenance on Sunday from 2-4 AM.',
            'A password reset was requested for your account. If this wasn\'t you, please contact support.',
            'You have received a new message from a potential buyer.',
            'Your payment has been processed successfully. Thank you for your business!',
            'Please verify your email address to activate all features of your account.'
        ]
        
        created_count = 0
        for i in range(count):
            title = random.choice(sample_titles)
            message = random.choice(sample_messages)
            notification_type = random.choice(notification_types)
            
            # Set is_read randomly (70% unread, 30% read)
            is_read = random.random() > 0.7
            
            # Create notification
            if broadcast:
                # Create broadcast notification (no specific user)
                notification = Notification.objects.create(
                    title=f"{title} (Broadcast)",
                    message=message,
                    type=notification_type,
                    is_read=is_read,
                    date=timezone.now()
                )
                self.stdout.write(self.style.SUCCESS(f'Created broadcast notification: {notification.title}'))
            else:
                # Create user-specific notification
                user = random.choice(users)
                notification = Notification.objects.create(
                    title=title,
                    message=message,
                    type=notification_type,
                    is_read=is_read,
                    user=user,
                    date=timezone.now()
                )
                self.stdout.write(self.style.SUCCESS(f'Created notification for {user.username}: {notification.title}'))
            
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} notifications'))
