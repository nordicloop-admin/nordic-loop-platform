"""
Test script for notifications API endpoints
"""
import os
import django
import json
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from notifications.models import Notification

User = get_user_model()

def get_tokens_for_user(user):
    """Generate JWT tokens for a user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def test_notifications_api():
    """Test the notifications API endpoints"""
    print("Testing Notifications API...")
    
    # Get or create a test user
    try:
        admin_user = User.objects.get(username='admin_test')
    except User.DoesNotExist:
        admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpassword123',
            is_staff=True,
            is_superuser=True,
            role='Admin'
        )
    
    try:
        regular_user = User.objects.get(username='user_test')
    except User.DoesNotExist:
        regular_user = User.objects.create_user(
            username='user_test',
            email='user@test.com',
            password='testpassword123',
            role='Staff'
        )
    
    # Get tokens for authentication
    admin_token = get_tokens_for_user(admin_user)
    user_token = get_tokens_for_user(regular_user)
    
    # Create API clients
    admin_client = APIClient()
    admin_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token['access']}")
    
    user_client = APIClient()
    user_client.credentials(HTTP_AUTHORIZATION=f"Bearer {user_token['access']}")
    
    # Clean up existing test notifications
    Notification.objects.filter(title__startswith='Test Notification').delete()
    
    # Test 1: Admin creates a notification for a specific user
    print("\n1. Admin creates a notification for a specific user")
    admin_response = admin_client.post('/api/notifications/create-notification/', {
        'title': 'Test Notification for User',
        'message': 'This is a test notification for a specific user',
        'type': 'info',
        'user': regular_user.id
    })
    print(f"Status: {admin_response.status_code}")
    try:
        print(f"Response: {admin_response.data}")
    except AttributeError:
        print(f"Response content: {admin_response.content.decode('utf-8')}")
    
    # Test 2: Admin creates a broadcast notification
    print("\n2. Admin creates a broadcast notification")
    admin_response = admin_client.post('/api/notifications/broadcast/', {
        'title': 'Test Broadcast Notification',
        'message': 'This is a test broadcast notification for all users',
        'type': 'info'
    })
    print(f"Status: {admin_response.status_code}")
    try:
        print(f"Response: {admin_response.data}")
    except AttributeError:
        print(f"Response content: {admin_response.content.decode('utf-8')}")
    
    # Test 3: Regular user gets their notifications
    print("\n3. Regular user gets their notifications")
    user_response = user_client.get('/api/notifications/')
    print(f"Status: {user_response.status_code}")
    try:
        print(f"Count: {len(user_response.data)}")
    except AttributeError:
        print(f"Response content: {user_response.content.decode('utf-8')}")
    
    # Test 4: Regular user gets unread notifications
    print("\n4. Regular user gets unread notifications")
    user_response = user_client.get('/api/notifications/unread/')
    print(f"Status: {user_response.status_code}")
    notification_id = None
    try:
        print(f"Count: {len(user_response.data)}")
        if user_response.data and len(user_response.data) > 0:
            notification_id = user_response.data[0]['id']
    except AttributeError:
        print(f"Response content: {user_response.content.decode('utf-8')}")
    
    # Test 5: Mark a notification as read
    if notification_id:
        print(f"\n5. Mark notification {notification_id} as read")
        user_response = user_client.put(f'/api/notifications/{notification_id}/read/')
        print(f"Status: {user_response.status_code}")
        try:
            print(f"Response: {user_response.data}")
        except AttributeError:
            print(f"Response content: {user_response.content.decode('utf-8')}")
    
    # Test 6: Mark all notifications as read
    print("\n6. Mark all notifications as read")
    user_response = user_client.put('/api/notifications/read-all/')
    print(f"Status: {user_response.status_code}")
    try:
        print(f"Response: {user_response.data}")
    except AttributeError:
        print(f"Response content: {user_response.content.decode('utf-8')}")
    
    # Test 7: Admin gets all notifications
    print("\n7. Admin gets all notifications")
    admin_response = admin_client.get('/api/notifications/list-all/')
    print(f"Status: {admin_response.status_code}")
    try:
        print(f"Count: {len(admin_response.data)}")
    except AttributeError:
        print(f"Response content: {admin_response.content.decode('utf-8')}")
    
    print("\nNotifications API testing completed!")

if __name__ == '__main__':
    test_notifications_api()
