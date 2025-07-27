#!/usr/bin/env python3
"""
Test the new admin ad approval and suspension functionality
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from ads.models import Ad, Location
from category.models import Category, SubCategory
from users.models import User

User = get_user_model()


def test_admin_functionality():
    """Test the complete admin functionality workflow"""
    print("🧪 Testing New Admin Ad Functionality")
    print("=" * 60)
    
    # Get the existing user
    try:
        admin_user = User.objects.get(email="karera@gmail.com")
        print(f"✅ Found admin user: {admin_user.username}")
        print(f"   - Is Staff: {admin_user.is_staff}")
        print(f"   - Is Superuser: {admin_user.is_superuser}")
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return
    
    # Create API client
    client = APIClient()
    
    # Generate JWT token
    refresh = RefreshToken.for_user(admin_user)
    access_token = str(refresh.access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Get or create test data
    category, _ = Category.objects.get_or_create(name="Test Category")
    subcategory, _ = SubCategory.objects.get_or_create(
        name="Test Subcategory", 
        category=category
    )
    location, _ = Location.objects.get_or_create(
        country="Sweden",
        city="Stockholm",
        state_province="Stockholm County"
    )
    
    # Create a test ad
    test_ad = Ad.objects.create(
        user=admin_user,
        category=category,
        subcategory=subcategory,
        specific_material="Test Material for Admin Testing",
        packaging="octabin",
        material_frequency="monthly",
        location=location,
        available_quantity=Decimal('100.00'),
        starting_bid_price=Decimal('50.00'),
        currency="EUR",
        title="Test Ad for Admin Actions",
        description="This is a test ad created for admin endpoint testing",
        is_complete=True,
        is_active=True,
        status='active'
    )
    
    print(f"\n📋 Created test ad:")
    print(f"   - ID: {test_ad.id}")
    print(f"   - Title: {test_ad.title}")
    print(f"   - Status: {test_ad.status}")
    print(f"   - Is Active: {test_ad.is_active}")
    print(f"   - Suspended by Admin: {test_ad.suspended_by_admin}")
    
    # Test 1: Admin Suspend Ad
    print(f"\n🔧 TEST 1: Admin Suspend Ad")
    print("-" * 40)
    
    suspend_url = f'/api/ads/admin/ads/{test_ad.id}/suspend/'
    print(f"POST {suspend_url}")
    
    response = client.post(suspend_url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Ad suspended successfully")
        response_data = response.json()
        print(f"Message: {response_data.get('message', 'No message')}")
        
        # Check ad status after suspension
        test_ad.refresh_from_db()
        print(f"Updated Ad Status:")
        print(f"   - Status: {test_ad.status}")
        print(f"   - Is Active: {test_ad.is_active}")
        print(f"   - Suspended by Admin: {test_ad.suspended_by_admin}")
        
        # Verify the expected changes
        assert test_ad.status == 'suspended', f"Expected status 'suspended', got '{test_ad.status}'"
        assert test_ad.suspended_by_admin == True, f"Expected suspended_by_admin True, got {test_ad.suspended_by_admin}"
        assert test_ad.is_active == False, f"Expected is_active False, got {test_ad.is_active}"
        print("✅ All status changes verified")
        
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Raw response: {response.content}")
        return
    
    # Test 2: Try to activate suspended ad (should fail)
    print(f"\n🔧 TEST 2: Try to Activate Suspended Ad (Should Fail)")
    print("-" * 40)
    
    activate_url = f'/api/ads/{test_ad.id}/activate/'
    print(f"POST {activate_url}")
    
    response = client.post(activate_url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ SUCCESS: Activation correctly blocked")
        response_data = response.json()
        print(f"Error Message: {response_data.get('error', 'No error message')}")
    else:
        print(f"❓ UNEXPECTED: Status {response.status_code}")
        try:
            response_data = response.json()
            print(f"Response: {response_data}")
        except:
            print(f"Raw response: {response.content}")
    
    # Test 3: Admin Approve Ad
    print(f"\n🔧 TEST 3: Admin Approve Ad")
    print("-" * 40)
    
    approve_url = f'/api/ads/admin/ads/{test_ad.id}/approve/'
    print(f"POST {approve_url}")
    
    response = client.post(approve_url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Ad approved successfully")
        response_data = response.json()
        print(f"Message: {response_data.get('message', 'No message')}")
        
        # Check ad status after approval
        test_ad.refresh_from_db()
        print(f"Updated Ad Status:")
        print(f"   - Status: {test_ad.status}")
        print(f"   - Is Active: {test_ad.is_active}")
        print(f"   - Suspended by Admin: {test_ad.suspended_by_admin}")
        
        # Verify the expected changes
        assert test_ad.status == 'active', f"Expected status 'active', got '{test_ad.status}'"
        assert test_ad.suspended_by_admin == False, f"Expected suspended_by_admin False, got {test_ad.suspended_by_admin}"
        print("✅ All status changes verified")
        
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Raw response: {response.content}")
        return
    
    # Test 4: Now try to activate ad (should work)
    print(f"\n🔧 TEST 4: Try to Activate Approved Ad (Should Work)")
    print("-" * 40)
    
    response = client.post(activate_url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS: Ad activated successfully after approval")
        response_data = response.json()
        print(f"Message: {response_data.get('message', 'No message')}")
        
        # Check final status
        test_ad.refresh_from_db()
        print(f"Final Ad Status:")
        print(f"   - Status: {test_ad.status}")
        print(f"   - Is Active: {test_ad.is_active}")
        print(f"   - Suspended by Admin: {test_ad.suspended_by_admin}")
        
    else:
        print(f"❓ Status {response.status_code}")
        try:
            response_data = response.json()
            print(f"Response: {response_data}")
        except:
            print(f"Raw response: {response.content}")
    
    # Test 5: Test with non-existent ad
    print(f"\n🔧 TEST 5: Test with Non-existent Ad")
    print("-" * 40)
    
    fake_url = f'/api/ads/admin/ads/99999/suspend/'
    response = client.post(fake_url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ SUCCESS: Correctly returns 404 for non-existent ad")
    else:
        print(f"❓ Status {response.status_code}")
    
    # Clean up
    print(f"\n🧹 Cleaning up test data...")
    test_ad.delete()
    print("✅ Test ad deleted")
    
    print(f"\n🎯 TESTING COMPLETE")
    print("-" * 40)
    print("✅ Admin suspend functionality tested")
    print("✅ Admin approve functionality tested")
    print("✅ User activation blocking tested")
    print("✅ User activation after approval tested")
    print("✅ Error handling tested")


if __name__ == "__main__":
    test_admin_functionality()
