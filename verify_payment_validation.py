#!/usr/bin/env python3
"""
Quick verification script to confirm ads cannot be activated without payment setup
"""

import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from ads.models import Ad
from company.models import Company
from category.models import Category
from django.core.exceptions import ValidationError

User = get_user_model()

# Create test data
timestamp = int(time.time())
username = f'verifyuser{timestamp}'

user = User.objects.create_user(
    username=username,
    email=f'{username}@test.com',
    password='testpass123'
)

company = Company.objects.create(
    official_name='Verify Company',
    user=user,
    payment_ready=False,  # Not payment ready
)

user.company = company
user.save()

category = Category.objects.get_or_create(name='Verify Category')[0]

ad = Ad.objects.create(
    title='Verify Ad',
    category=category,
    user=user,
    is_complete=True,
    is_active=False,
    starting_bid_price=50.00,
    available_quantity=5,
    currency='EUR'
)

print(f"Created ad with ID {ad.id}")
print(f"Initial state: is_active={ad.is_active}, is_complete={ad.is_complete}")
print(f"Company payment_ready: {company.payment_ready}")

# Try to activate the ad
try:
    print("\n--- Attempting to activate ad ---")
    ad.is_active = True
    ad.save()
    
    # Check actual database state
    ad.refresh_from_db()
    print(f"After save attempt: is_active={ad.is_active}")
    
    if ad.is_active:
        print("❌ FAILED: Ad was activated despite payment not ready!")
    else:
        print("✅ SUCCESS: Ad remained inactive (payment validation worked)")
        
except ValidationError as e:
    print(f"✅ SUCCESS: ValidationError raised: {e}")
    # Check that ad wasn't saved
    ad.refresh_from_db()
    print(f"Database state after error: is_active={ad.is_active}")

print("\n--- Testing with payment ready company ---")
company.payment_ready = True
company.stripe_account_id = 'acct_test123'
company.stripe_capabilities_complete = True
company.stripe_onboarding_complete = True
company.save()

try:
    ad.is_active = True
    ad.save()
    ad.refresh_from_db()
    print(f"Payment ready company - ad activated: is_active={ad.is_active}")
    if ad.is_active:
        print("✅ SUCCESS: Ad activated with payment ready company")
    else:
        print("❌ ISSUE: Ad not activated even with payment ready company")
except ValidationError as e:
    print(f"❌ UNEXPECTED: ValidationError with payment ready company: {e}")

# Cleanup
print("\n--- Cleanup ---")
ad.delete()
company.delete() 
user.delete()
print("✓ Test data cleaned up")