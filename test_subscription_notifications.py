#!/usr/bin/env python3
"""
Test script for subscription-based notification targeting
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from company.models import Company
from ads.models import Subscription
from notifications.models import Notification

User = get_user_model()

def create_test_data():
    """Create test companies, users, and subscriptions"""
    print("Creating test data...")
    
    # Create test companies
    companies = []
    for i, plan in enumerate(['free', 'standard', 'premium'], 1):
        company, created = Company.objects.get_or_create(
            official_name=f"Test Company {plan.title()}",
            defaults={
                'vat_number': f'VAT{i:06d}',
                'email': f'company{i}@test.com',
                'sector': 'manufacturing  & Production',
                'country': 'Sweden',
                'website': f'http://company{i}.test.com',
                'status': 'approved'
            }
        )
        companies.append(company)
        
        # Create subscription for the company
        subscription, created = Subscription.objects.get_or_create(
            company=company,
            defaults={
                'plan': plan,
                'status': 'active',
                'start_date': datetime.now().date(),
                'end_date': datetime.now().date() + timedelta(days=30),
                'auto_renew': True,
                'last_payment': datetime.now().date(),
                'amount': '99.99' if plan != 'free' else '0.00',
                'contact_name': f'Contact {i}',
                'contact_email': f'contact{i}@test.com'
            }
        )
        
        # Create test users for each company
        for j in range(2):  # 2 users per company
            user, created = User.objects.get_or_create(
                username=f'user_{plan}_{j+1}',
                defaults={
                    'email': f'user_{plan}_{j+1}@test.com',
                    'first_name': f'User{j+1}',
                    'last_name': f'{plan.title()}',
                    'company': company,
                    'role': 'Staff'
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
    
    print(f"Created {len(companies)} companies with subscriptions and users")
    return companies

def test_subscription_targeting():
    """Test subscription-based notification targeting"""
    print("\n=== Testing Subscription-Based Notification Targeting ===")
    
    # Create test data
    companies = create_test_data()
    
    # Test 1: Create notification for all users
    print("\n1. Testing 'All Users' targeting...")
    all_notification = Notification.objects.create(
        title="Welcome to Nordic Loop",
        message="This notification goes to all users regardless of subscription.",
        type="system",
        priority="normal",
        subscription_target="all",
        user=None  # Broadcast to all
    )
    print(f"Created notification ID {all_notification.id} for all users")
    
    # Test 2: Create notification for free plan users
    print("\n2. Testing 'Free Plan' targeting...")
    free_users = User.objects.filter(company__subscriptions__plan='free', company__subscriptions__status='active')
    print(f"Found {free_users.count()} free plan users")
    
    for user in free_users:
        free_notification = Notification.objects.create(
            title="Free Plan Special Offer",
            message="Upgrade to premium and get 50% off your first month!",
            type="promotion",
            priority="normal",
            subscription_target="free",
            user=user
        )
    print(f"Created {free_users.count()} notifications for free plan users")
    
    # Test 3: Create notification for premium plan users
    print("\n3. Testing 'Premium Plan' targeting...")
    premium_users = User.objects.filter(company__subscriptions__plan='premium', company__subscriptions__status='active')
    print(f"Found {premium_users.count()} premium plan users")
    
    for user in premium_users:
        premium_notification = Notification.objects.create(
            title="Premium Feature Update",
            message="New advanced analytics features are now available in your premium dashboard!",
            type="feature",
            priority="high",
            subscription_target="premium",
            user=user
        )
    print(f"Created {premium_users.count()} notifications for premium plan users")
    
    # Test 4: Create notification for standard plan users
    print("\n4. Testing 'Standard Plan' targeting...")
    standard_users = User.objects.filter(company__subscriptions__plan='standard', company__subscriptions__status='active')
    print(f"Found {standard_users.count()} standard plan users")
    
    for user in standard_users:
        standard_notification = Notification.objects.create(
            title="Standard Plan Update",
            message="Your monthly report is ready for download.",
            type="system",
            priority="normal",
            subscription_target="standard",
            user=user
        )
    print(f"Created {standard_users.count()} notifications for standard plan users")
    
    # Summary
    print("\n=== Summary ===")
    total_notifications = Notification.objects.count()
    print(f"Total notifications created: {total_notifications}")
    
    for target in ['all', 'free', 'standard', 'premium']:
        count = Notification.objects.filter(subscription_target=target).count()
        print(f"Notifications targeting '{target}': {count}")
    
    print("\n=== Test completed successfully! ===")

if __name__ == "__main__":
    test_subscription_targeting()
