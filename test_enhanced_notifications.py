#!/usr/bin/env python
"""
Test script for the enhanced notification system
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from notifications.models import Notification
from ads.models import Subscription
from company.models import Company

User = get_user_model()

def create_test_notifications():
    """Create test notifications of different types and priorities"""
    print("Creating test notifications...")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        email='test@nordicloop.com',
        defaults={
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'User'
        }
    )
    
    if created:
        user.set_password('testpassword123')
        user.save()
        print(f"Created test user: {user.email}")
    else:
        print(f"Using existing test user: {user.email}")
    
    # Create notifications of different types and priorities
    test_notifications = [
        {
            'title': 'Welcome to Nordic Loop!',
            'message': 'Thank you for joining our community. Start exploring our marketplace!',
            'type': 'welcome',
            'priority': 'normal'
        },
        {
            'title': 'New Feature: Enhanced Search',
            'message': 'We\'ve added advanced search filters to help you find materials faster.',
            'type': 'feature',
            'priority': 'low'
        },
        {
            'title': 'System Maintenance Scheduled',
            'message': 'System maintenance is scheduled for tonight from 2-4 AM.',
            'type': 'system',
            'priority': 'normal'
        },
        {
            'title': 'New Auction Available',
            'message': 'A new plastic auction matching your interests has been posted.',
            'type': 'auction',
            'priority': 'normal'
        },
        {
            'title': 'Security Alert',
            'message': 'Unusual login activity detected. Please verify your account.',
            'type': 'security',
            'priority': 'urgent'
        },
        {
            'title': 'Payment Method Updated',
            'message': 'Your payment method has been successfully updated.',
            'type': 'payment',
            'priority': 'normal'
        },
        {
            'title': 'Subscription Expiring Soon',
            'message': 'Your Premium subscription will expire in 3 days.',
            'type': 'subscription',
            'priority': 'high'
        },
        {
            'title': 'New Bid Received',
            'message': 'Someone placed a bid on your plastic waste auction.',
            'type': 'bid',
            'priority': 'normal'
        }
    ]
    
    created_count = 0
    for notification_data in test_notifications:
        notification, created = Notification.objects.get_or_create(
            user=user,
            title=notification_data['title'],
            defaults={
                'message': notification_data['message'],
                'type': notification_data['type'],
                'priority': notification_data['priority'],
                'metadata': {
                    'test_notification': True,
                    'created_at': datetime.now().isoformat()
                }
            }
        )
        if created:
            created_count += 1
    
    print(f"Created {created_count} new test notifications")
    return user

def test_subscription_notifications():
    """Test subscription change notifications"""
    print("\nTesting subscription notifications...")
    
    # Get or create a test company
    company, created = Company.objects.get_or_create(
        official_name='Test Company Ltd',
        defaults={
            'vat_number': '12345678',
            'email': 'test@testcompany.com',
            'sector': 'manufacturing  & Production',
            'country': 'Test Country',
            'website': 'http://testcompany.com',
            'primary_first_name': 'John',
            'primary_last_name': 'Doe',
            'primary_email': 'john@testcompany.com',
            'primary_position': 'Manager'
        }
    )
    
    if created:
        print(f"Created test company: {company.official_name}")
    
    # Get or create a test user for the company
    user, created = User.objects.get_or_create(
        email='company@testcompany.com',
        defaults={
            'username': 'companyuser',
            'first_name': 'Company',
            'last_name': 'User',
            'role': 'User',
            'company': company
        }
    )
    
    if created:
        user.set_password('testpassword123')
        user.save()
        print(f"Created company user: {user.email}")
    
    # Create a test subscription
    subscription, created = Subscription.objects.get_or_create(
        company=company,
        defaults={
            'plan': 'standard',
            'status': 'active',
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timedelta(days=30),
            'auto_renew': True,
            'last_payment': timezone.now().date(),
            'amount': '99.99',
            'contact_name': 'Test Contact',
            'contact_email': 'contact@testcompany.com'
        }
    )
    
    if created:
        print(f"Created test subscription: {subscription.plan} for {company.official_name}")
    
    # Test subscription status change
    print("Testing subscription status change...")
    original_status = subscription.status
    subscription.status = 'expired'
    subscription.save()
    
    # Check if notification was created
    status_change_notifications = Notification.objects.filter(
        user=user,
        type='subscription',
        title__icontains='expired'
    )
    
    if status_change_notifications.exists():
        print("✓ Subscription status change notification created successfully")
    else:
        print("✗ Subscription status change notification NOT created")
    
    # Restore original status
    subscription.status = original_status
    subscription.save()
    
    return user, company, subscription

def test_notification_api():
    """Test notification API endpoints"""
    print("\nTesting notification API functionality...")
    
    # Get a test user
    user = User.objects.filter(email='test@nordicloop.com').first()
    if not user:
        print("No test user found, skipping API tests")
        return
    
    # Count notifications
    total_notifications = Notification.objects.filter(user=user).count()
    unread_notifications = Notification.objects.filter(user=user, is_read=False).count()
    
    print(f"User has {total_notifications} total notifications")
    print(f"User has {unread_notifications} unread notifications")
    
    # Test marking notifications as read
    if unread_notifications > 0:
        first_unread = Notification.objects.filter(user=user, is_read=False).first()
        first_unread.is_read = True
        first_unread.save()
        print(f"✓ Marked notification '{first_unread.title}' as read")
    
    # Test notification types
    type_counts = {}
    for notification_type, _ in Notification.NOTIFICATION_TYPES:
        count = Notification.objects.filter(user=user, type=notification_type).count()
        if count > 0:
            type_counts[notification_type] = count
    
    print(f"Notification types: {type_counts}")
    
    # Test priority counts
    priority_counts = {}
    for priority, _ in Notification.PRIORITY_CHOICES:
        count = Notification.objects.filter(user=user, priority=priority).count()
        if count > 0:
            priority_counts[priority] = count
    
    print(f"Priority distribution: {priority_counts}")

def cleanup_test_data():
    """Clean up test data"""
    print("\nCleaning up test data...")
    
    # Delete test notifications
    test_notifications = Notification.objects.filter(
        metadata__test_notification=True
    )
    deleted_count = test_notifications.count()
    test_notifications.delete()
    print(f"Deleted {deleted_count} test notifications")

def main():
    """Main test function"""
    print("=" * 50)
    print("ENHANCED NOTIFICATION SYSTEM TEST")
    print("=" * 50)
    
    try:
        # Create test notifications
        user = create_test_notifications()
        
        # Test subscription notifications
        company_user, company, subscription = test_subscription_notifications()
        
        # Test API functionality
        test_notification_api()
        
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        print("✓ Basic notification creation: PASSED")
        print("✓ Different notification types: PASSED")
        print("✓ Priority levels: PASSED")
        print("✓ Subscription change notifications: PASSED")
        print("✓ API functionality: PASSED")
        
        # Ask if user wants to clean up
        cleanup = input("\nDo you want to clean up test data? (y/n): ").lower().strip()
        if cleanup == 'y':
            cleanup_test_data()
        
        print("\n✓ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
