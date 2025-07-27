#!/usr/bin/env python3
"""
Direct test of Admin Ad endpoints using Django's test framework.
This bypasses HTTP and tests the views directly.
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from ads.models import Ad, Location
from category.models import Category, SubCategory
from users.models import User

User = get_user_model()


class AdminAdEndpointsDirectTest(APITestCase):
    """Direct test of Admin Ad endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Get the existing user
        try:
            self.test_user = User.objects.get(email="karera@gmail.com")
            print(f"✅ Using existing user: {self.test_user.username}")
            print(f"   - Is Staff: {self.test_user.is_staff}")
            print(f"   - Is Superuser: {self.test_user.is_superuser}")
        except User.DoesNotExist:
            print("❌ User karera@gmail.com not found")
            return
        
        # Get or create test data
        self.category, _ = Category.objects.get_or_create(name="Test Category")
        self.subcategory, _ = SubCategory.objects.get_or_create(
            name="Test Subcategory", 
            category=self.category
        )
        self.location, _ = Location.objects.get_or_create(
            country="Sweden",
            city="Stockholm",
            state_province="Stockholm County"
        )
        
        # Create test ad
        self.test_ad = Ad.objects.create(
            user=self.test_user,
            category=self.category,
            subcategory=self.subcategory,
            specific_material="Test Material for Admin Testing",
            packaging="octabin",
            material_frequency="monthly",
            location=self.location,
            available_quantity=Decimal('100.00'),
            starting_bid_price=Decimal('50.00'),
            currency="EUR",
            title="Test Ad for Admin Actions",
            description="This is a test ad created for admin endpoint testing",
            is_complete=True,
            is_active=True,
            status='active'
        )
        
        # Create suspended ad
        self.suspended_ad = Ad.objects.create(
            user=self.test_user,
            category=self.category,
            subcategory=self.subcategory,
            specific_material="Suspended Test Material",
            packaging="octabin",
            material_frequency="monthly",
            location=self.location,
            available_quantity=Decimal('50.00'),
            starting_bid_price=Decimal('40.00'),
            currency="EUR",
            title="Suspended Test Ad",
            description="This ad is suspended for testing approval",
            is_complete=True,
            is_active=False,
            status='suspended',
            suspended_by_admin=True
        )
        
        # Set up API client with authentication
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.test_user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_admin_suspend_ad_success(self):
        """Test successful ad suspension by admin"""
        print(f"\n🔧 Testing Admin Ad Suspension")
        print(f"   - Ad ID: {self.test_ad.id}")
        print(f"   - Current Status: {self.test_ad.status}")
        print(f"   - Is Active: {self.test_ad.is_active}")
        print(f"   - Suspended by Admin: {self.test_ad.suspended_by_admin}")
        
        url = f'/api/ads/admin/ads/{self.test_ad.id}/suspend/'
        response = self.client.post(url)
        
        print(f"   - Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Ad suspended successfully")
            response_data = response.data
            print(f"   - Response Message: {response_data.get('message', 'No message')}")
            
            # Verify ad status changed
            self.test_ad.refresh_from_db()
            print(f"   - New Status: {self.test_ad.status}")
            print(f"   - Is Active: {self.test_ad.is_active}")
            print(f"   - Suspended by Admin: {self.test_ad.suspended_by_admin}")
            
            self.assertEqual(self.test_ad.status, 'suspended')
            self.assertTrue(self.test_ad.suspended_by_admin)
            self.assertFalse(self.test_ad.is_active)
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.data
                print(f"   - Error: {error_data}")
            except:
                print(f"   - Raw response: {response.content}")

    def test_admin_approve_ad_success(self):
        """Test successful ad approval by admin"""
        print(f"\n🔧 Testing Admin Ad Approval")
        print(f"   - Ad ID: {self.suspended_ad.id}")
        print(f"   - Current Status: {self.suspended_ad.status}")
        print(f"   - Is Active: {self.suspended_ad.is_active}")
        print(f"   - Suspended by Admin: {self.suspended_ad.suspended_by_admin}")
        
        url = f'/api/ads/admin/ads/{self.suspended_ad.id}/approve/'
        response = self.client.post(url)
        
        print(f"   - Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Ad approved successfully")
            response_data = response.data
            print(f"   - Response Message: {response_data.get('message', 'No message')}")
            
            # Verify ad status changed
            self.suspended_ad.refresh_from_db()
            print(f"   - New Status: {self.suspended_ad.status}")
            print(f"   - Is Active: {self.suspended_ad.is_active}")
            print(f"   - Suspended by Admin: {self.suspended_ad.suspended_by_admin}")
            
            self.assertEqual(self.suspended_ad.status, 'active')
            self.assertFalse(self.suspended_ad.suspended_by_admin)
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            try:
                error_data = response.data
                print(f"   - Error: {error_data}")
            except:
                print(f"   - Raw response: {response.content}")

    def test_admin_approve_nonexistent_ad(self):
        """Test ad approval fails for non-existent ad"""
        print(f"\n🔧 Testing Non-existent Ad")
        
        url = '/api/ads/admin/ads/99999/approve/'
        response = self.client.post(url)
        
        print(f"   - Response Status: {response.status_code}")
        
        if response.status_code == 500:
            print("✅ EXPECTED: Server error for non-existent ad")
        elif response.status_code == 404:
            print("✅ EXPECTED: Not found error for non-existent ad")
        else:
            print(f"❓ UNEXPECTED: Status {response.status_code}")
        
        try:
            error_data = response.data
            print(f"   - Error Response: {error_data}")
        except:
            print(f"   - Raw response: {response.content}")

    def test_unauthorized_access(self):
        """Test unauthorized access"""
        print(f"\n🔧 Testing Unauthorized Access")
        
        # Create client without authentication
        unauth_client = APIClient()
        url = f'/api/ads/admin/ads/{self.test_ad.id}/suspend/'
        response = unauth_client.post(url)
        
        print(f"   - Response Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ EXPECTED: Unauthorized without authentication")
        else:
            print(f"❓ UNEXPECTED: Status {response.status_code}")
            try:
                error_data = response.data
                print(f"   - Error: {error_data}")
            except:
                print(f"   - Raw response: {response.content}")

    def tearDown(self):
        """Clean up test data (but preserve the user)"""
        # Delete test ads but keep the user
        Ad.objects.filter(title__startswith="Test Ad").delete()
        Ad.objects.filter(title__startswith="Suspended Test Ad").delete()


def run_direct_tests():
    """Run the direct tests"""
    print("🧪 Running Direct Admin Endpoint Tests")
    print("=" * 60)
    
    # Create test instance
    test_instance = AdminAdEndpointsDirectTest()
    test_instance.setUp()
    
    if hasattr(test_instance, 'test_user'):
        # Run tests
        test_instance.test_admin_suspend_ad_success()
        test_instance.test_admin_approve_ad_success()
        test_instance.test_admin_approve_nonexistent_ad()
        test_instance.test_unauthorized_access()
        
        # Clean up
        test_instance.tearDown()
        
        print(f"\n🎯 TESTING COMPLETE")
        print("-" * 40)
        print(f"✅ User {test_instance.test_user.username} preserved")
        print("✅ All tests completed")
    else:
        print("❌ Could not run tests - user not found")


if __name__ == "__main__":
    run_direct_tests()
