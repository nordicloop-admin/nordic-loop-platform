#!/usr/bin/env python3
"""
Test script to verify ad update functionality.
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from ads.models import Ad
from ads.services import AdService
from ads.repository import AdRepository
from users.models import User

def test_ad_update_functionality():
    """Test the ad update functionality"""
    
    print("🧪 Testing Ad Update Functionality")
    print("=" * 50)
    
    # Get a test user and ad
    user = User.objects.first()
    if not user:
        print("❌ No users found. Please create test data first.")
        return
    
    # Get an ad owned by the user
    ad = Ad.objects.filter(user=user).first()
    if not ad:
        print("❌ No ads found for user. Please create test data first.")
        return
    
    print(f"📋 Testing with Ad ID: {ad.id}")
    print(f"👤 User: {user.username}")
    print(f"📝 Original Title: {ad.title}")
    print("-" * 50)
    
    # Initialize service
    ad_repository = AdRepository()
    ad_service = AdService(ad_repository)
    
    # Test 1: Partial update (only title and description)
    print("\n🔄 Test 1: Partial Update (title & description)")
    update_data = {
        "title": "Updated Title - Test Update Functionality",
        "description": "This is an updated description to test the partial update functionality. The description is long enough to pass validation."
    }
    
    try:
        updated_ad = ad_service.partial_update_ad(ad.id, update_data, user=user)
        print(f"✅ Partial update successful!")
        print(f"📝 New Title: {updated_ad.title}")
        print(f"📄 New Description: {updated_ad.description[:50]}...")
    except Exception as e:
        print(f"❌ Partial update failed: {e}")
    
    # Test 2: Update pricing information
    print("\n🔄 Test 2: Update Pricing Information")
    pricing_data = {
        "starting_bid_price": 99.99,
        "reserve_price": 150.00,
        "currency": "USD"
    }
    
    try:
        updated_ad = ad_service.partial_update_ad(ad.id, pricing_data, user=user)
        print(f"✅ Pricing update successful!")
        print(f"💰 Starting Price: {updated_ad.starting_bid_price} {updated_ad.currency}")
        print(f"💎 Reserve Price: {updated_ad.reserve_price} {updated_ad.currency}")
    except Exception as e:
        print(f"❌ Pricing update failed: {e}")
    
    # Test 3: Update location
    print("\n🔄 Test 3: Update Location")
    location_data = {
        "location_data": {
            "country": "Sweden",
            "state_province": "Västra Götaland",
            "city": "Gothenburg",
            "address_line": "Test Street 123",
            "postal_code": "41234"
        }
    }
    
    try:
        updated_ad = ad_service.partial_update_ad(ad.id, location_data, user=user)
        print(f"✅ Location update successful!")
        if updated_ad.location:
            print(f"📍 Location: {updated_ad.location.city}, {updated_ad.location.country}")
    except Exception as e:
        print(f"❌ Location update failed: {e}")
    
    # Test 4: Complete update with validation
    print("\n🔄 Test 4: Complete Update with Validation")
    complete_data = {
        "title": "Complete Update Test - Premium Material",
        "description": "This is a complete update test with all required fields. The material is high-quality and ready for processing.",
        "available_quantity": 50.0,
        "starting_bid_price": 75.50,
        "minimum_order_quantity": 5.0,
        "currency": "EUR",
        "auction_duration": 14
    }
    
    try:
        updated_ad = ad_service.update_complete_ad(ad.id, complete_data, user=user)
        print(f"✅ Complete update successful!")
        print(f"📦 Quantity: {updated_ad.available_quantity} {updated_ad.unit_of_measurement}")
        print(f"💰 Price: {updated_ad.starting_bid_price} {updated_ad.currency}")
        print(f"⏰ Duration: {updated_ad.auction_duration} days")
    except Exception as e:
        print(f"❌ Complete update failed: {e}")
    
    # Test 5: Update with invalid data (should fail)
    print("\n🔄 Test 5: Invalid Update (should fail)")
    invalid_data = {
        "starting_bid_price": 100.0,
        "reserve_price": 50.0  # Reserve price lower than starting price
    }
    
    try:
        updated_ad = ad_service.partial_update_ad(ad.id, invalid_data, user=user)
        print(f"❌ Update should have failed but didn't!")
    except Exception as e:
        print(f"✅ Update correctly failed with validation: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Ad Update Functionality Tests Completed!")
    
    # Show final ad state
    final_ad = Ad.objects.get(id=ad.id)
    print(f"\n📊 Final Ad State:")
    print(f"   Title: {final_ad.title}")
    print(f"   Description: {final_ad.description[:50]}...")
    print(f"   Price: {final_ad.starting_bid_price} {final_ad.currency}")
    print(f"   Quantity: {final_ad.available_quantity} {final_ad.unit_of_measurement}")
    print(f"   Current Step: {final_ad.current_step}")
    print(f"   Is Complete: {final_ad.is_complete}")

if __name__ == "__main__":
    test_ad_update_functionality() 