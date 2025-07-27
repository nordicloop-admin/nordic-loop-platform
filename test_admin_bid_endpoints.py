#!/usr/bin/env python3
"""
Test admin bid endpoints functionality
"""

import os
import django
import requests
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from ads.models import Ad, Location
from category.models import Category, SubCategory
from bids.models import Bid
from users.models import User

User = get_user_model()


def test_admin_bid_endpoints():
    """Test admin bid endpoints functionality"""
    print("🧪 Testing Admin Bid Endpoints")
    print("=" * 60)
    
    # Get the existing admin user
    try:
        admin_user = User.objects.get(email="karera@gmail.com")
        print(f"✅ Found admin user: {admin_user.username}")
        print(f"   - Is Staff: {admin_user.is_staff}")
        print(f"   - Is Superuser: {admin_user.is_superuser}")
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return
    
    # Create regular users for bidding (multiple users since each user can only have one bid per ad)
    regular_user_1, created1 = User.objects.get_or_create(
        username="testbidder1",
        defaults={
            "email": "testbidder1@example.com",
            "first_name": "Test",
            "last_name": "Bidder1"
        }
    )
    if created1:
        regular_user_1.set_password("testpass123")
        regular_user_1.save()
        print(f"✅ Created regular user 1: {regular_user_1.username}")
    else:
        print(f"✅ Using existing regular user 1: {regular_user_1.username}")

    regular_user_2, created2 = User.objects.get_or_create(
        username="testbidder2",
        defaults={
            "email": "testbidder2@example.com",
            "first_name": "Test",
            "last_name": "Bidder2"
        }
    )
    if created2:
        regular_user_2.set_password("testpass123")
        regular_user_2.save()
        print(f"✅ Created regular user 2: {regular_user_2.username}")
    else:
        print(f"✅ Using existing regular user 2: {regular_user_2.username}")

    regular_user_3, created3 = User.objects.get_or_create(
        username="testbidder3",
        defaults={
            "email": "testbidder3@example.com",
            "first_name": "Test",
            "last_name": "Bidder3"
        }
    )
    if created3:
        regular_user_3.set_password("testpass123")
        regular_user_3.save()
        print(f"✅ Created regular user 3: {regular_user_3.username}")
    else:
        print(f"✅ Using existing regular user 3: {regular_user_3.username}")
    
    # Generate JWT tokens
    admin_refresh = RefreshToken.for_user(admin_user)
    admin_access_token = str(admin_refresh.access_token)
    
    # Set up headers
    admin_headers = {
        'Authorization': f'Bearer {admin_access_token}',
        'Content-Type': 'application/json'
    }
    
    base_url = 'http://localhost:8000'
    
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
        specific_material="Test Material for Bid Testing",
        packaging="octabin",
        material_frequency="monthly",
        location=location,
        available_quantity=Decimal('100.00'),
        starting_bid_price=Decimal('50.00'),
        currency="EUR",
        title="Test Ad for Bid Actions",
        description="This is a test ad created for bid endpoint testing",
        is_complete=True,
        is_active=True,
        status='active'
    )
    
    # Create a test bid
    test_bid = Bid.objects.create(
        user=regular_user_1,
        ad=test_ad,
        bid_price_per_unit=Decimal('55.00'),
        volume_requested=Decimal('20.00'),
        volume_type='partial',
        status='active',
        notes='Test bid for admin actions'
    )
    
    print(f"\n📋 Created test data:")
    print(f"   - Ad ID: {test_ad.id}")
    print(f"   - Ad Title: {test_ad.title}")
    print(f"   - Bid ID: {test_bid.id}")
    print(f"   - Bid Price: {test_bid.bid_price_per_unit}")
    print(f"   - Bid Status: {test_bid.status}")
    print(f"   - Bidder: {test_bid.user.username}")
    
    # Test 1: Admin Approve Bid
    print(f"\n🔧 TEST 1: Admin Approve Bid")
    print("-" * 40)
    
    approve_url = f'{base_url}/api/bids/admin/bids/{test_bid.id}/approve/'
    print(f"POST {approve_url}")
    
    try:
        response = requests.post(approve_url, headers=admin_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Bid approved successfully")
            response_data = response.json()
            print(f"Message: {response_data.get('message', 'No message')}")
            
            # Check bid status after approval
            test_bid.refresh_from_db()
            print(f"Updated Bid Status: {test_bid.status}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Admin Reject Bid
    print(f"\n🔧 TEST 2: Admin Reject Bid")
    print("-" * 40)
    
    # Create another bid to reject
    test_bid_2 = Bid.objects.create(
        user=regular_user_2,
        ad=test_ad,
        bid_price_per_unit=Decimal('52.00'),
        volume_requested=Decimal('15.00'),
        volume_type='partial',
        status='active',
        notes='Test bid 2 for rejection'
    )
    
    reject_url = f'{base_url}/api/bids/admin/bids/{test_bid_2.id}/reject/'
    print(f"POST {reject_url}")
    
    try:
        response = requests.post(reject_url, headers=admin_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Bid rejected successfully")
            response_data = response.json()
            print(f"Message: {response_data.get('message', 'No message')}")
            
            # Check bid status after rejection
            test_bid_2.refresh_from_db()
            print(f"Updated Bid Status: {test_bid_2.status}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Admin Mark Bid as Won
    print(f"\n🔧 TEST 3: Admin Mark Bid as Won")
    print("-" * 40)
    
    # Create another bid to mark as won
    test_bid_3 = Bid.objects.create(
        user=regular_user_3,
        ad=test_ad,
        bid_price_per_unit=Decimal('60.00'),
        volume_requested=Decimal('25.00'),
        volume_type='partial',
        status='active',
        notes='Test bid 3 for winning'
    )
    
    mark_won_url = f'{base_url}/api/bids/admin/bids/{test_bid_3.id}/mark-as-won/'
    print(f"POST {mark_won_url}")
    
    try:
        response = requests.post(mark_won_url, headers=admin_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Bid marked as won successfully")
            response_data = response.json()
            print(f"Message: {response_data.get('message', 'No message')}")
            
            # Check bid status after marking as won
            test_bid_3.refresh_from_db()
            print(f"Updated Bid Status: {test_bid_3.status}")
            
            # Check if other bids were marked as lost
            other_bids = Bid.objects.filter(ad=test_ad).exclude(id=test_bid_3.id)
            print(f"Other bids status:")
            for bid in other_bids:
                print(f"   - Bid {bid.id}: {bid.status}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Test with non-existent bid
    print(f"\n🔧 TEST 4: Test with Non-existent Bid")
    print("-" * 40)
    
    fake_url = f'{base_url}/api/bids/admin/bids/99999/approve/'
    try:
        response = requests.post(fake_url, headers=admin_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ SUCCESS: Correctly returns 400 for non-existent bid")
            response_data = response.json()
            print(f"Error: {response_data.get('error', 'No error message')}")
        else:
            print(f"❓ Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 5: Test without authentication
    print(f"\n🔧 TEST 5: Test without Authentication")
    print("-" * 40)
    
    try:
        response = requests.post(approve_url)  # No headers
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ SUCCESS: Correctly returns 401 for unauthenticated request")
        else:
            print(f"❓ Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 6: Test admin bid list endpoint
    print(f"\n🔧 TEST 6: Test Admin Bid List")
    print("-" * 40)
    
    list_url = f'{base_url}/api/bids/admin/bids/'
    try:
        response = requests.get(list_url, headers=admin_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Admin bid list retrieved")
            response_data = response.json()
            print(f"Total bids: {response_data.get('total', 'Unknown')}")
            print(f"Current page: {response_data.get('current_page', 'Unknown')}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Clean up
    print(f"\n🧹 Cleaning up test data...")
    Bid.objects.filter(ad=test_ad).delete()
    test_ad.delete()
    # Clean up created users
    if created1:
        regular_user_1.delete()
    if created2:
        regular_user_2.delete()
    if created3:
        regular_user_3.delete()
    print("✅ Test data cleaned up")
    
    print(f"\n🎯 TESTING COMPLETE")
    print("-" * 40)
    print("✅ Admin bid approve functionality tested")
    print("✅ Admin bid reject functionality tested")
    print("✅ Admin bid mark as won functionality tested")
    print("✅ Error handling tested")
    print("✅ Authentication tested")
    print("✅ Admin bid list tested")


if __name__ == "__main__":
    test_admin_bid_endpoints()
