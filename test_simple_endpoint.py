#!/usr/bin/env python3
"""
Simple test to verify basic endpoint functionality
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


def test_basic_endpoints():
    """Test basic endpoint functionality"""
    print("🧪 Testing Basic Endpoint Functionality")
    print("=" * 50)
    
    # Get the existing user
    try:
        test_user = User.objects.get(email="karera@gmail.com")
        print(f"✅ Found user: {test_user.username}")
        print(f"   - Is Staff: {test_user.is_staff}")
        print(f"   - Is Superuser: {test_user.is_superuser}")
    except User.DoesNotExist:
        print("❌ User not found")
        return
    
    # Create API client
    client = APIClient()
    
    # Generate JWT token
    refresh = RefreshToken.for_user(test_user)
    access_token = str(refresh.access_token)
    
    # Test 1: Test a working endpoint first (GET request)
    print(f"\n🔧 TEST 1: Testing working GET endpoint")
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    response = client.get('/api/ads/user/')
    print(f"   - GET /api/ads/user/ Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ GET endpoint works fine")
    else:
        print(f"❌ GET endpoint failed: {response.status_code}")
        return
    
    # Test 2: Test a simple POST endpoint
    print(f"\n🔧 TEST 2: Testing POST endpoint (ad activation)")
    # Find an ad to test with
    from ads.models import Ad
    test_ad = Ad.objects.filter(user=test_user).first()
    
    if test_ad:
        print(f"   - Testing with ad ID: {test_ad.id}")
        response = client.post(f'/api/ads/{test_ad.id}/activate/')
        print(f"   - POST /api/ads/{test_ad.id}/activate/ Status: {response.status_code}")
        
        if response.status_code in [200, 400]:  # 400 might be expected if ad is incomplete
            print("✅ POST endpoint is reachable")
        else:
            print(f"❌ POST endpoint failed: {response.status_code}")
    else:
        print("   - No ads found to test with")
    
    # Test 3: Test admin endpoints with detailed debugging
    print(f"\n🔧 TEST 3: Testing admin endpoints with debugging")
    
    if test_ad:
        # Test suspend endpoint
        print(f"   - Testing suspend endpoint")
        suspend_url = f'/api/ads/admin/ads/{test_ad.id}/suspend/'
        print(f"   - URL: {suspend_url}")
        
        try:
            response = client.post(suspend_url)
            print(f"   - Status Code: {response.status_code}")
            print(f"   - Response Headers: {dict(response.items())}")
            
            if hasattr(response, 'data'):
                print(f"   - Response Data: {response.data}")
            else:
                print(f"   - Response Content: {response.content}")
                
        except Exception as e:
            print(f"   - Exception occurred: {e}")
        
        # Test approve endpoint
        print(f"   - Testing approve endpoint")
        approve_url = f'/api/ads/admin/ads/{test_ad.id}/approve/'
        print(f"   - URL: {approve_url}")
        
        try:
            response = client.post(approve_url)
            print(f"   - Status Code: {response.status_code}")
            print(f"   - Response Headers: {dict(response.items())}")
            
            if hasattr(response, 'data'):
                print(f"   - Response Data: {response.data}")
            else:
                print(f"   - Response Content: {response.content}")
                
        except Exception as e:
            print(f"   - Exception occurred: {e}")
    
    # Test 4: Check URL patterns
    print(f"\n🔧 TEST 4: Checking URL patterns")
    from django.urls import reverse
    from django.conf import settings
    
    try:
        # Try to reverse the URL patterns
        print("   - Checking URL patterns...")
        from django.urls import resolve
        
        if test_ad:
            suspend_path = f'/api/ads/admin/ads/{test_ad.id}/suspend/'
            approve_path = f'/api/ads/admin/ads/{test_ad.id}/approve/'
            
            try:
                suspend_match = resolve(suspend_path)
                print(f"   - Suspend URL resolves to: {suspend_match.func}")
                print(f"   - Suspend URL name: {suspend_match.url_name}")
            except Exception as e:
                print(f"   - Suspend URL resolution failed: {e}")
            
            try:
                approve_match = resolve(approve_path)
                print(f"   - Approve URL resolves to: {approve_match.func}")
                print(f"   - Approve URL name: {approve_match.url_name}")
            except Exception as e:
                print(f"   - Approve URL resolution failed: {e}")
                
    except Exception as e:
        print(f"   - URL pattern check failed: {e}")
    
    print(f"\n🎯 DEBUGGING COMPLETE")


if __name__ == "__main__":
    test_basic_endpoints()
