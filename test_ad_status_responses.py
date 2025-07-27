#!/usr/bin/env python3
"""
Test ad status responses to verify that suspended status is properly returned
"""

import os
import django
import requests
import json
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from ads.models import Ad, Location
from category.models import Category, SubCategory
from users.models import User

User = get_user_model()


def test_ad_status_responses():
    """Test that ad status responses include suspended status"""
    print("🧪 Testing Ad Status Responses")
    print("=" * 60)
    
    # Get the existing admin user
    try:
        admin_user = User.objects.get(email="karera@gmail.com")
        print(f"✅ Found admin user: {admin_user.username}")
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return
    
    # Generate JWT token
    refresh = RefreshToken.for_user(admin_user)
    access_token = str(refresh.access_token)
    
    # Set up headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    base_url = 'http://localhost:8000'
    
    # Get or create test data
    category, _ = Category.objects.get_or_create(name="Test Status Category")
    subcategory, _ = SubCategory.objects.get_or_create(
        name="Test Status Subcategory", 
        category=category
    )
    location, _ = Location.objects.get_or_create(
        country="Sweden",
        city="Stockholm",
        state_province="Stockholm County"
    )
    
    # Create test ads with different statuses
    print(f"\n📋 Creating test ads with different statuses...")
    
    # 1. Active ad
    active_ad = Ad.objects.create(
        user=admin_user,
        category=category,
        subcategory=subcategory,
        specific_material="Active Test Material",
        packaging="octabin",
        material_frequency="monthly",
        location=location,
        available_quantity=Decimal('100.00'),
        starting_bid_price=Decimal('50.00'),
        currency="EUR",
        title="Active Test Ad",
        description="This is an active test ad",
        is_complete=True,
        is_active=True,
        status='active'
    )
    print(f"✅ Created active ad: ID {active_ad.id}")
    
    # 2. Suspended ad
    suspended_ad = Ad.objects.create(
        user=admin_user,
        category=category,
        subcategory=subcategory,
        specific_material="Suspended Test Material",
        packaging="octabin",
        material_frequency="monthly",
        location=location,
        available_quantity=Decimal('75.00'),
        starting_bid_price=Decimal('45.00'),
        currency="EUR",
        title="Suspended Test Ad",
        description="This is a suspended test ad",
        is_complete=True,
        is_active=False,
        status='suspended',
        suspended_by_admin=True
    )
    print(f"✅ Created suspended ad: ID {suspended_ad.id}")
    
    # 3. Inactive ad (not suspended, just deactivated by user)
    inactive_ad = Ad.objects.create(
        user=admin_user,
        category=category,
        subcategory=subcategory,
        specific_material="Inactive Test Material",
        packaging="octabin",
        material_frequency="monthly",
        location=location,
        available_quantity=Decimal('50.00'),
        starting_bid_price=Decimal('40.00'),
        currency="EUR",
        title="Inactive Test Ad",
        description="This is an inactive test ad",
        is_complete=True,
        is_active=False,
        status='active'  # Status is active but is_active is False
    )
    print(f"✅ Created inactive ad: ID {inactive_ad.id}")
    
    # Test 1: List ads using AdListSerializer
    print(f"\n🔧 TEST 1: List Ads (AdListSerializer)")
    print("-" * 40)
    
    list_url = f'{base_url}/api/ads/user/'
    print(f"GET {list_url}")
    
    try:
        response = requests.get(list_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Ads list retrieved")
            response_data = response.json()
            
            # Find our test ads in the response
            for ad_data in response_data:
                if ad_data['id'] == active_ad.id:
                    print(f"   Active Ad (ID {active_ad.id}):")
                    print(f"     - status: {ad_data.get('status', 'NOT FOUND')}")
                    print(f"     - is_active: {ad_data.get('is_active', 'NOT FOUND')}")
                    print(f"     - suspended_by_admin: {ad_data.get('suspended_by_admin', 'NOT FOUND')}")
                
                elif ad_data['id'] == suspended_ad.id:
                    print(f"   Suspended Ad (ID {suspended_ad.id}):")
                    print(f"     - status: {ad_data.get('status', 'NOT FOUND')}")
                    print(f"     - is_active: {ad_data.get('is_active', 'NOT FOUND')}")
                    print(f"     - suspended_by_admin: {ad_data.get('suspended_by_admin', 'NOT FOUND')}")
                
                elif ad_data['id'] == inactive_ad.id:
                    print(f"   Inactive Ad (ID {inactive_ad.id}):")
                    print(f"     - status: {ad_data.get('status', 'NOT FOUND')}")
                    print(f"     - is_active: {ad_data.get('is_active', 'NOT FOUND')}")
                    print(f"     - suspended_by_admin: {ad_data.get('suspended_by_admin', 'NOT FOUND')}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Get individual ad details using AdCompleteSerializer
    print(f"\n🔧 TEST 2: Get Ad Details (AdCompleteSerializer)")
    print("-" * 40)
    
    detail_url = f'{base_url}/api/ads/{suspended_ad.id}/'
    print(f"GET {detail_url}")
    
    try:
        response = requests.get(detail_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Ad details retrieved")
            response_data = response.json()
            print(f"   Suspended Ad Details:")
            print(f"     - status: {response_data.get('status', 'NOT FOUND')}")
            print(f"     - is_active: {response_data.get('is_active', 'NOT FOUND')}")
            print(f"     - suspended_by_admin: {response_data.get('suspended_by_admin', 'NOT FOUND')}")
            print(f"     - title: {response_data.get('title', 'NOT FOUND')}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 3: Admin auction list using AdminAuctionListSerializer
    print(f"\n🔧 TEST 3: Admin Auction List (AdminAuctionListSerializer)")
    print("-" * 40)
    
    admin_list_url = f'{base_url}/api/ads/admin/auctions/'
    print(f"GET {admin_list_url}")
    
    try:
        response = requests.get(admin_list_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Admin auction list retrieved")
            response_data = response.json()
            
            # Find our test ads in the response
            ads_data = response_data.get('results', response_data)  # Handle pagination
            for ad_data in ads_data:
                if ad_data['id'] == active_ad.id:
                    print(f"   Active Ad (ID {active_ad.id}):")
                    print(f"     - status: {ad_data.get('status', 'NOT FOUND')}")
                
                elif ad_data['id'] == suspended_ad.id:
                    print(f"   Suspended Ad (ID {suspended_ad.id}):")
                    print(f"     - status: {ad_data.get('status', 'NOT FOUND')}")
                
                elif ad_data['id'] == inactive_ad.id:
                    print(f"   Inactive Ad (ID {inactive_ad.id}):")
                    print(f"     - status: {ad_data.get('status', 'NOT FOUND')}")
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 4: Test admin suspend/approve workflow
    print(f"\n🔧 TEST 4: Test Admin Suspend/Approve Workflow")
    print("-" * 40)
    
    # Suspend the active ad
    suspend_url = f'{base_url}/api/ads/admin/ads/{active_ad.id}/suspend/'
    print(f"POST {suspend_url}")
    
    try:
        response = requests.post(suspend_url, headers=headers)
        print(f"Suspend Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Ad suspended")
            
            # Now check the status in the list
            response = requests.get(admin_list_url, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                ads_data = response_data.get('results', response_data)
                for ad_data in ads_data:
                    if ad_data['id'] == active_ad.id:
                        print(f"   After suspension - status: {ad_data.get('status', 'NOT FOUND')}")
                        break
            
            # Approve it back
            approve_url = f'{base_url}/api/ads/admin/ads/{active_ad.id}/approve/'
            response = requests.post(approve_url, headers=headers)
            print(f"Approve Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS: Ad approved")
                
                # Check status again
                response = requests.get(admin_list_url, headers=headers)
                if response.status_code == 200:
                    response_data = response.json()
                    ads_data = response_data.get('results', response_data)
                    for ad_data in ads_data:
                        if ad_data['id'] == active_ad.id:
                            print(f"   After approval - status: {ad_data.get('status', 'NOT FOUND')}")
                            break
        
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Clean up
    print(f"\n🧹 Cleaning up test data...")
    active_ad.delete()
    suspended_ad.delete()
    inactive_ad.delete()
    print("✅ Test ads cleaned up")
    
    print(f"\n🎯 TESTING COMPLETE")
    print("-" * 40)
    print("✅ Ad list status field tested")
    print("✅ Ad detail status field tested")
    print("✅ Admin auction list status tested")
    print("✅ Admin suspend/approve workflow tested")


if __name__ == "__main__":
    test_ad_status_responses()
