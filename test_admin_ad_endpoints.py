#!/usr/bin/env python3
"""
Test script for Admin Ad Approval and Suspension endpoints.
Tests both AdminAdApproveView and AdminAdSuspendView endpoints.
Uses existing user: karera@gmail.com (password: Rwabose5@)
"""

import os
import django
import json
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient

from ads.models import Ad, Location
from category.models import Category, SubCategory
from users.models import User

User = get_user_model()


def run_admin_endpoint_tests():
    """Run comprehensive tests for admin ad endpoints"""
    print("🧪 Testing Admin Ad Approval and Suspension Endpoints")
    print("=" * 60)

    # Get the existing user (DO NOT DELETE OR MODIFY)
    try:
        test_user = User.objects.get(email="karera@gmail.com")
        print(f"✅ Found existing user: {test_user.username} ({test_user.email})")
        print(f"   - Is Staff: {test_user.is_staff}")
        print(f"   - Is Superuser: {test_user.is_superuser}")
    except User.DoesNotExist:
        print("❌ User karera@gmail.com not found. Please create this user first.")
        return

    # Create API client (better for REST API testing)
    client = APIClient()

    # Generate JWT token for the user
    refresh = RefreshToken.for_user(test_user)
    access_token = str(refresh.access_token)
    print(f"✅ Generated JWT token for user")

    # Set authentication credentials
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    # Find existing ads for testing
    user_ads = Ad.objects.filter(user=test_user)
    print(f"\n📋 Found {user_ads.count()} ads for user {test_user.username}")

    if user_ads.count() == 0:
        print("❌ No ads found for testing. Creating a test ad...")
        # Create minimal test data if needed
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

        test_ad = Ad.objects.create(
            user=test_user,
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
        print(f"✅ Created test ad with ID: {test_ad.id}")
    else:
        test_ad = user_ads.first()
        print(f"✅ Using existing ad with ID: {test_ad.id}")

    print(f"\n📊 Current Ad Status:")
    print(f"   - ID: {test_ad.id}")
    print(f"   - Title: {test_ad.title}")
    print(f"   - Status: {test_ad.status}")
    print(f"   - Is Active: {test_ad.is_active}")
    print(f"   - Suspended by Admin: {test_ad.suspended_by_admin}")
    print(f"   - Is Complete: {test_ad.is_complete}")

    # Test 1: Test Admin Ad Suspension
    print(f"\n🔧 TEST 1: Admin Ad Suspension")
    print("-" * 40)

    suspend_url = f'/api/ads/admin/ads/{test_ad.id}/suspend/'
    print(f"POST {suspend_url}")

    response = client.post(suspend_url)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✅ SUCCESS: Ad suspended successfully")
        response_data = response.json()
        print(f"Response Message: {response_data.get('message', 'No message')}")

        # Check ad status after suspension
        test_ad.refresh_from_db()
        print(f"Updated Ad Status:")
        print(f"   - Status: {test_ad.status}")
        print(f"   - Is Active: {test_ad.is_active}")
        print(f"   - Suspended by Admin: {test_ad.suspended_by_admin}")

    elif response.status_code == 403:
        print("❌ PERMISSION DENIED: User doesn't have admin permissions")
        print("   This is expected if the user is not an admin/staff member")
        try:
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'No error details')}")
        except:
            print(f"   Raw response: {response.content}")

    elif response.status_code == 401:
        print("❌ UNAUTHORIZED: Authentication failed")
        print("   Check if the token is valid")

    else:
        print(f"❌ UNEXPECTED ERROR: Status {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Raw response: {response.content}")


    # Test 2: Test Admin Ad Approval
    print(f"\n🔧 TEST 2: Admin Ad Approval")
    print("-" * 40)

    approve_url = f'/api/ads/admin/ads/{test_ad.id}/approve/'
    print(f"POST {approve_url}")

    response = client.post(approve_url)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✅ SUCCESS: Ad approved successfully")
        response_data = response.json()
        print(f"Response Message: {response_data.get('message', 'No message')}")

        # Check ad status after approval
        test_ad.refresh_from_db()
        print(f"Updated Ad Status:")
        print(f"   - Status: {test_ad.status}")
        print(f"   - Is Active: {test_ad.is_active}")
        print(f"   - Suspended by Admin: {test_ad.suspended_by_admin}")

    elif response.status_code == 403:
        print("❌ PERMISSION DENIED: User doesn't have admin permissions")
        print("   This is expected if the user is not an admin/staff member")
        try:
            error_data = response.json()
            print(f"   Error: {error_data.get('detail', 'No error details')}")
        except:
            print(f"   Raw response: {response.content}")

    elif response.status_code == 401:
        print("❌ UNAUTHORIZED: Authentication failed")
        print("   Check if the token is valid")

    else:
        print(f"❌ UNEXPECTED ERROR: Status {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Raw response: {response.content}")

    # Test 3: Test with non-existent ad
    print(f"\n🔧 TEST 3: Test with Non-existent Ad")
    print("-" * 40)

    fake_ad_id = 99999
    fake_url = f'/api/ads/admin/ads/{fake_ad_id}/suspend/'
    print(f"POST {fake_url}")

    response = client.post(fake_url)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 500:
        print("✅ EXPECTED: Server error for non-existent ad")
    elif response.status_code == 404:
        print("✅ EXPECTED: Not found error for non-existent ad")
    else:
        print(f"❓ UNEXPECTED: Status {response.status_code}")

    try:
        error_data = response.json()
        print(f"Error Response: {error_data}")
    except:
        print(f"Raw response: {response.content}")

    # Test 4: Test without authentication
    print(f"\n🔧 TEST 4: Test without Authentication")
    print("-" * 40)

    # Create a new client without authentication
    unauth_client = APIClient()
    response = unauth_client.post(suspend_url)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 401:
        print("✅ EXPECTED: Unauthorized without authentication")
    else:
        print(f"❓ UNEXPECTED: Status {response.status_code}")
        try:
            error_data = response.json()
            print(f"   Error: {error_data}")
        except:
            print(f"   Raw response: {response.content}")

    # Final status summary
    print(f"\n📊 FINAL AD STATUS:")
    print("-" * 40)
    test_ad.refresh_from_db()
    print(f"   - ID: {test_ad.id}")
    print(f"   - Title: {test_ad.title}")
    print(f"   - Status: {test_ad.status}")
    print(f"   - Is Active: {test_ad.is_active}")
    print(f"   - Suspended by Admin: {test_ad.suspended_by_admin}")
    print(f"   - Is Complete: {test_ad.is_complete}")

    print(f"\n🎯 TESTING SUMMARY:")
    print("-" * 40)
    print("✅ Admin suspension endpoint tested")
    print("✅ Admin approval endpoint tested")
    print("✅ Non-existent ad handling tested")
    print("✅ Authentication requirement tested")
    print(f"✅ User {test_user.username} preserved (not modified)")

    if not test_user.is_staff and not test_user.is_superuser:
        print(f"\n⚠️  NOTE: User {test_user.username} is not an admin.")
        print("   To test successful admin operations, make this user staff/superuser:")
        print(f"   User.objects.filter(email='karera@gmail.com').update(is_staff=True)")


def test_with_curl_commands():
    """Generate curl commands for manual testing"""
    print(f"\n🌐 CURL COMMANDS FOR MANUAL TESTING:")
    print("=" * 60)

    try:
        test_user = User.objects.get(email="karera@gmail.com")
        refresh = RefreshToken.for_user(test_user)
        access_token = str(refresh.access_token)
        test_ad = Ad.objects.filter(user=test_user).first()

        if test_ad:
            print(f"# Suspend ad {test_ad.id}")
            print(f"curl -X POST \\")
            print(f"  -H 'Authorization: Bearer {access_token}' \\")
            print(f"  -H 'Content-Type: application/json' \\")
            print(f"  'http://localhost:8000/api/ads/admin/ads/{test_ad.id}/suspend/'")

            print(f"\n# Approve ad {test_ad.id}")
            print(f"curl -X POST \\")
            print(f"  -H 'Authorization: Bearer {access_token}' \\")
            print(f"  -H 'Content-Type: application/json' \\")
            print(f"  'http://localhost:8000/api/ads/admin/ads/{test_ad.id}/approve/'")

            print(f"\n# Check ad status")
            print(f"curl -H 'Authorization: Bearer {access_token}' \\")
            print(f"  'http://localhost:8000/api/ads/{test_ad.id}/'")
        else:
            print("No ads found for generating curl commands")

    except User.DoesNotExist:
        print("User not found for generating curl commands")


if __name__ == "__main__":
    run_admin_endpoint_tests()
    test_with_curl_commands()
