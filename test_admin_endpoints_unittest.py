#!/usr/bin/env python3
"""
Unit test for Admin Ad endpoints using Django's unittest framework.
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


class AdminAdEndpointsTest(APITestCase):
    """Test Admin Ad endpoints"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data once for the entire test class"""
        # Get the existing user
        try:
            cls.test_user = User.objects.get(email="karera@gmail.com")
            print(f"✅ Using existing user: {cls.test_user.username}")
            print(f"   - Is Staff: {cls.test_user.is_staff}")
            print(f"   - Is Superuser: {cls.test_user.is_superuser}")
        except User.DoesNotExist:
            print("❌ User karera@gmail.com not found")
            raise
        
        # Get or create test data
        cls.category, _ = Category.objects.get_or_create(name="Test Category")
        cls.subcategory, _ = SubCategory.objects.get_or_create(
            name="Test Subcategory", 
            category=cls.category
        )
        cls.location, _ = Location.objects.get_or_create(
            country="Sweden",
            city="Stockholm",
            state_province="Stockholm County"
        )
    
    def setUp(self):
        """Set up for each test"""
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
        
        url = f'/api/ads/admin/ads/{self.test_ad.id}/suspend/'
        response = self.client.post(url)
        
        print(f"   - Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Ad suspended successfully")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('message', response.data)
            self.assertEqual(response.data['message'], "Ad suspended successfully by administrator")
            
            # Verify ad status changed
            self.test_ad.refresh_from_db()
            self.assertEqual(self.test_ad.status, 'suspended')
            self.assertTrue(self.test_ad.suspended_by_admin)
            self.assertFalse(self.test_ad.is_active)
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            if hasattr(response, 'data'):
                print(f"   - Error: {response.data}")
            else:
                print(f"   - Raw response: {response.content}")
            # Still run assertions to see the actual failure
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_approve_ad_success(self):
        """Test successful ad approval by admin"""
        print(f"\n🔧 Testing Admin Ad Approval")
        print(f"   - Ad ID: {self.suspended_ad.id}")
        print(f"   - Current Status: {self.suspended_ad.status}")
        
        url = f'/api/ads/admin/ads/{self.suspended_ad.id}/approve/'
        response = self.client.post(url)
        
        print(f"   - Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Ad approved successfully")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('message', response.data)
            self.assertEqual(response.data['message'], "Ad approved successfully by administrator")
            
            # Verify ad status changed
            self.suspended_ad.refresh_from_db()
            self.assertEqual(self.suspended_ad.status, 'active')
            self.assertFalse(self.suspended_ad.suspended_by_admin)
            
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            if hasattr(response, 'data'):
                print(f"   - Error: {response.data}")
            else:
                print(f"   - Raw response: {response.content}")
            # Still run assertions to see the actual failure
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_approve_nonexistent_ad(self):
        """Test ad approval fails for non-existent ad"""
        print(f"\n🔧 Testing Non-existent Ad")
        
        url = '/api/ads/admin/ads/99999/approve/'
        response = self.client.post(url)
        
        print(f"   - Response Status: {response.status_code}")
        
        # Should return 500 or 404
        self.assertIn(response.status_code, [404, 500])

    def test_unauthorized_access(self):
        """Test unauthorized access"""
        print(f"\n🔧 Testing Unauthorized Access")
        
        # Create client without authentication
        unauth_client = APIClient()
        url = f'/api/ads/admin/ads/{self.test_ad.id}/suspend/'
        response = unauth_client.post(url)
        
        print(f"   - Response Status: {response.status_code}")
        
        # Should return 401 Unauthorized
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def tearDown(self):
        """Clean up after each test"""
        # Delete test ads
        Ad.objects.filter(title__startswith="Test Ad").delete()
        Ad.objects.filter(title__startswith="Suspended Test Ad").delete()


if __name__ == "__main__":
    import unittest
    
    print("🧪 Running Admin Endpoint Unit Tests")
    print("=" * 60)
    
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(AdminAdEndpointsTest)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n🎯 TEST RESULTS:")
    print("-" * 40)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
