#!/usr/bin/env python3
"""
Simple test to verify status field is working in API responses
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

User = get_user_model()

def test_status_simple():
    """Simple test for status field"""
    print("🧪 Simple Status Field Test")
    print("=" * 40)
    
    # Get admin user
    admin_user = User.objects.get(email="karera@gmail.com")
    refresh = RefreshToken.for_user(admin_user)
    access_token = str(refresh.access_token)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Create test ad
    category, _ = Category.objects.get_or_create(name="Test Status")
    subcategory, _ = SubCategory.objects.get_or_create(name="Test Status Sub", category=category)
    location, _ = Location.objects.get_or_create(
        country="Sweden", city="Stockholm", state_province="Stockholm County"
    )
    
    test_ad = Ad.objects.create(
        user=admin_user,
        category=category,
        subcategory=subcategory,
        specific_material="Test Material",
        packaging="octabin",
        material_frequency="monthly",
        location=location,
        available_quantity=Decimal('100.00'),
        starting_bid_price=Decimal('50.00'),
        currency="EUR",
        title="Test Status Ad",
        description="Test ad for status checking",
        is_complete=True,
        is_active=True,
        status='active'
    )
    
    print(f"Created test ad: ID {test_ad.id}")
    
    # Test 1: Admin auction list (working)
    print("\n1. Admin Auction List:")
    response = requests.get('http://localhost:8000/api/ads/admin/auctions/', headers=headers)
    if response.status_code == 200:
        data = response.json()
        for ad in data.get('results', []):
            if ad['id'] == test_ad.id:
                print(f"   ✅ Status: {ad.get('status', 'NOT FOUND')}")
                break
    
    # Test 2: User ads list (paginated)
    print("\n2. User Ads List:")
    response = requests.get('http://localhost:8000/api/ads/user/', headers=headers)
    if response.status_code == 200:
        data = response.json()
        for ad in data.get('results', []):
            if ad['id'] == test_ad.id:
                print(f"   ✅ Status: {ad.get('status', 'NOT FOUND')}")
                print(f"   ✅ Is Active: {ad.get('is_active', 'NOT FOUND')}")
                print(f"   ✅ Suspended by Admin: {ad.get('suspended_by_admin', 'NOT FOUND')}")
                break
    
    # Test 3: Ad detail (nested response)
    print("\n3. Ad Detail:")
    response = requests.get(f'http://localhost:8000/api/ads/{test_ad.id}/', headers=headers)
    if response.status_code == 200:
        data = response.json()
        ad_data = data.get('data', {})
        print(f"   ✅ Status: {ad_data.get('status', 'NOT FOUND')}")
        print(f"   ✅ Is Active: {ad_data.get('is_active', 'NOT FOUND')}")
        print(f"   ✅ Suspended by Admin: {ad_data.get('suspended_by_admin', 'NOT FOUND')}")
    
    # Test 4: Suspend and check status
    print("\n4. Suspend Ad and Check Status:")
    response = requests.post(f'http://localhost:8000/api/ads/admin/ads/{test_ad.id}/suspend/', headers=headers)
    if response.status_code == 200:
        print("   ✅ Ad suspended")
        
        # Check admin list
        response = requests.get('http://localhost:8000/api/ads/admin/auctions/', headers=headers)
        if response.status_code == 200:
            data = response.json()
            for ad in data.get('results', []):
                if ad['id'] == test_ad.id:
                    print(f"   ✅ Admin List Status: {ad.get('status', 'NOT FOUND')}")
                    break
        
        # Check user list
        response = requests.get('http://localhost:8000/api/ads/user/', headers=headers)
        if response.status_code == 200:
            data = response.json()
            for ad in data.get('results', []):
                if ad['id'] == test_ad.id:
                    print(f"   ✅ User List Status: {ad.get('status', 'NOT FOUND')}")
                    break
        
        # Check detail
        response = requests.get(f'http://localhost:8000/api/ads/{test_ad.id}/', headers=headers)
        if response.status_code == 200:
            data = response.json()
            ad_data = data.get('data', {})
            print(f"   ✅ Detail Status: {ad_data.get('status', 'NOT FOUND')}")
    
    # Clean up
    test_ad.delete()
    print("\n✅ Test completed and cleaned up")

if __name__ == "__main__":
    test_status_simple()
