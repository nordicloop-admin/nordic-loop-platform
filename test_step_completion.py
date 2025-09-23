#!/usr/bin/env python
"""
Test script     print(f"Ad details:")
    print(f"  Title: {ad.title}")
    print(f"  Category: {ad.category}")
    print(f"  Type: {getattr(ad, 'ad_type', 'auction')}")
    print(f"  Material Type: {ad.material_type}")
    print(f"  Weight: {ad.weight}")
    print(f"  Starting Price: {ad.starting_price}")p completion fields functionality.
Run this from the nordic-loop-platform directory.
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from ads.models import Ad
from django.contrib.auth.models import User

def test_step_completion():
    print("=== Testing Step Completion Fields ===")
    
    # Get or create a test ad
    ads = Ad.objects.all()[:1]
    if ads:
        ad = ads[0]
        print(f"Using existing ad: {ad.id} - '{ad.title}'")
    else:
        user = User.objects.first()
        if not user:
            print("Creating test user...")
            user = User.objects.create_user('testuser', 'test@test.com', 'testpass')
        
        print("Creating test ad...")
        ad = Ad.objects.create(
            user=user,
            title="Test Step Completion Ad",
            description="Testing step completion",
            category="metal"
        )
        print(f"Created ad: {ad.id}")
    
    print(f"\nAd details:")
    print(f"  Title: {ad.title}")
    print(f"  Category: {ad.category}")
    print(f"  Type: {getattr(ad, 'ad_type', 'auction')}")
    print(f"  Available Quantity: {getattr(ad, 'available_quantity', 'None')}")
    print(f"  Starting Bid Price: {getattr(ad, 'starting_bid_price', 'None')}")
    print(f"  Reserve Price: {getattr(ad, 'reserve_price', 'None')}")
    
    # Check current step completion
    print(f"\n=== Current Step Completion ===")
    status = ad.get_step_completion_status()
    print(f"Completion Status: {status}")
    
    print(f"\nIndividual Step Flags:")
    for i in range(1, 9):
        field_name = f'step_{i}_complete'
        value = getattr(ad, field_name, 'NOT_FOUND')
        print(f"  {field_name}: {value}")
    
    # Update the ad to complete more steps
    print(f"\n=== Updating Ad to Complete More Steps ===")
    # Update fields that would complete various steps
    ad.specifications = "Aluminum scrap, clean material"
    if ad.available_quantity is None:
        ad.available_quantity = 100
    if ad.minimum_order_quantity is None:
        ad.minimum_order_quantity = 10
    ad.packaging = "baled"
    ad.city = "Stockholm"
    ad.latitude = 59.3293
    ad.longitude = 18.0686
    if ad.starting_bid_price is None:
        ad.starting_bid_price = 25.00
    if ad.reserve_price is None:
        ad.reserve_price = 100.00
    ad.auction_duration = 7
    
    # Save the ad (this should trigger step completion update)
    print("Saving ad (should trigger step completion update)...")
    ad.save()
    
    # Check updated step completion
    print(f"\n=== After Save (Auto Step Update) ===")
    status_after_save = ad.get_step_completion_status()
    print(f"Completion Status: {status_after_save}")
    
    print(f"\nStep Flags After Save:")
    for i in range(1, 9):
        field_name = f'step_{i}_complete'
        value = getattr(ad, field_name, 'NOT_FOUND')
        print(f"  {field_name}: {value}")
    
    # Test manual step completion update
    print(f"\n=== Manual Step Completion Update ===")
    ad.update_step_completion_flags()
    status_manual = ad.get_step_completion_status()
    print(f"Completion Status After Manual Update: {status_manual}")
    
    print(f"\nFinal Step Flags:")
    for i in range(1, 9):
        field_name = f'step_{i}_complete'
        value = getattr(ad, field_name, 'NOT_FOUND')
        print(f"  {field_name}: {value}")
    
    # Count completed steps
    completed_count = sum(1 for i in range(1, 9) if getattr(ad, f'step_{i}_complete', False))
    print(f"\nTotal Completed Steps: {completed_count}/8")
    
    print(f"\n✅ Step completion test completed!")
    return ad

if __name__ == "__main__":
    test_step_completion()