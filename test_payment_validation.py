#!/usr/bin/env python3
"""
Test script for payment readiness validation system
Tests all aspects of the payment validation implementation
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.http import JsonResponse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from ads.models import Ad
from company.models import Company
from category.models import Category
from company.payment_utils import (
    check_stripe_account_capabilities,
    validate_auction_publication,
    requires_payment_ready_company
)
import json

User = get_user_model()

class PaymentValidationTester:
    def __init__(self):
        self.client = APIClient()
        self.factory = RequestFactory()
        self.test_results = []
        
    def create_test_data(self):
        """Create test user, company, and ad data"""
        print("Creating test data...")
        
        # Clean up any existing test data first
        User.objects.filter(username__startswith='testseller').delete()
        
        # Create test user with timestamp to ensure uniqueness
        import time
        timestamp = int(time.time())
        username = f'testseller{timestamp}'
        
        self.user = User.objects.create_user(
            username=username,
            email=f'testseller{timestamp}@test.com',
            password='testpass123'
        )
        
        # Create company without payment setup
        self.company = Company.objects.create(
            official_name='Test Company',
            user=self.user,
            payment_ready=False,  # No payment setup
            stripe_account_id=None,
            stripe_capabilities_complete=False,
            stripe_onboarding_complete=False
        )
        
        # Associate user with company
        self.user.company = self.company
        self.user.save()
        
        # Create category for ad
        self.category = Category.objects.get_or_create(name='Test Category')[0]
        
        # Create test ad
        self.ad = Ad.objects.create(
            title='Test Ad',
            category=self.category,
            user=self.user,
            is_complete=True,
            is_active=False,  # Not yet activated
            starting_bid_price=100.00,
            available_quantity=10,
            currency='EUR'
        )
        
        # Get authentication token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        print(f"Created test user: {self.user.username}")
        print(f"Created test company: {self.company.official_name} (payment_ready: {self.company.payment_ready})")
        print(f"Created test ad: {self.ad.title} (id: {self.ad.id}, is_active: {self.ad.is_active})")

    def test_model_validation(self):
        """Test Ad model validation prevents activation without payment setup"""
        print("\n--- Testing Ad Model Validation ---")
        
        try:
            print(f"Before save: is_active={self.ad.is_active}, is_complete={self.ad.is_complete}")
            print(f"Company payment_ready: {self.company.payment_ready}")
            
            # Try to activate ad directly through model
            self.ad.is_active = True
            self.ad.save()  # Should raise ValidationError
            
            # If we get here, the save succeeded when it shouldn't have
            # Check if the ad was actually saved as active
            self.ad.refresh_from_db()
            print(f"After save: is_active={self.ad.is_active}, is_complete={self.ad.is_complete}")
            
            if self.ad.is_active:
                self.test_results.append({
                    'test': 'Model validation - should prevent activation',
                    'status': 'FAILED',
                    'error': 'Ad was activated and saved despite company not being payment ready'
                })
            else:
                self.test_results.append({
                    'test': 'Model validation - should prevent activation',
                    'status': 'PASSED',
                    'error': 'Ad activation was prevented (is_active remained False)'
                })
                
        except Exception as e:
            self.test_results.append({
                'test': 'Model validation - should prevent activation', 
                'status': 'PASSED',
                'error': f'ValidationError correctly raised: {str(e)}'
            })
            print(f"✓ Model validation correctly prevented activation: {e}")

    def test_decorator_functionality(self):
        """Test the requires_payment_ready_company decorator"""
        print("\n--- Testing Decorator Functionality ---")
        
        @requires_payment_ready_company
        def mock_view(request):
            return JsonResponse({'message': 'Success'})
        
        # Create mock request
        request = self.factory.post('/test/')
        request.user = self.user
        
        try:
            response = mock_view(request)
            
            self.test_results.append({
                'test': 'Decorator - should block unpaid company',
                'status': 'FAILED', 
                'error': 'Decorator allowed access despite company not being payment ready'
            })
        except Exception as e:
            self.test_results.append({
                'test': 'Decorator - should block unpaid company',
                'status': 'PASSED',
                'error': str(e)
            })
            print(f"✓ Decorator correctly blocked unpaid company: {e}")

    def test_api_endpoint_protection(self):
        """Test that the ad activation API endpoint is protected"""
        print("\n--- Testing API Endpoint Protection ---")
        
        # Try to activate ad via API
        response = self.client.post(f'/api/ads/{self.ad.id}/activate/')
        
        if response.status_code == 403:
            self.test_results.append({
                'test': 'API endpoint protection',
                'status': 'PASSED',
                'error': f'API correctly returned 403: {response.data}'
            })
            print(f"✓ API correctly blocked activation: {response.data}")
        else:
            self.test_results.append({
                'test': 'API endpoint protection',
                'status': 'FAILED',
                'error': f'API allowed activation with status {response.status_code}: {response.data}'
            })
            print(f"✗ API unexpectedly allowed activation: {response.status_code} - {response.data}")

    def test_marketplace_filtering(self):
        """Test that marketplace only shows ads from payment-ready companies"""
        print("\n--- Testing Marketplace Filtering ---")
        
        # First, try to bypass validation and create an active ad (for testing filtering)
        Ad.objects.filter(id=self.ad.id).update(is_active=True)  # Bypass model validation
        
        # Get marketplace listings
        response = self.client.get('/api/ads/?complete=true')
        
        if response.status_code == 200:
            ads_data = response.data.get('results', [])
            found_test_ad = any(ad['id'] == self.ad.id for ad in ads_data)
            
            if not found_test_ad:
                self.test_results.append({
                    'test': 'Marketplace filtering',
                    'status': 'PASSED',
                    'error': 'Marketplace correctly filtered out ads from non-payment-ready companies'
                })
                print("✓ Marketplace correctly filtered out unpaid company's ads")
            else:
                self.test_results.append({
                    'test': 'Marketplace filtering', 
                    'status': 'FAILED',
                    'error': 'Marketplace showed ad from non-payment-ready company'
                })
                print("✗ Marketplace incorrectly showed unpaid company's ad")
        else:
            self.test_results.append({
                'test': 'Marketplace filtering',
                'status': 'ERROR',
                'error': f'Failed to get marketplace listings: {response.status_code}'
            })

    def test_payment_ready_company_flow(self):
        """Test that everything works when company is payment ready"""
        print("\n--- Testing Payment Ready Company Flow ---")
        
        # Update company to be payment ready
        self.company.payment_ready = True
        self.company.stripe_account_id = 'acct_test123'
        self.company.stripe_capabilities_complete = True
        self.company.stripe_onboarding_complete = True
        self.company.save()
        
        # Reset ad to inactive
        Ad.objects.filter(id=self.ad.id).update(is_active=False)
        
        # Try API activation again
        response = self.client.post(f'/api/ads/{self.ad.id}/activate/')
        
        if response.status_code == 200:
            self.test_results.append({
                'test': 'Payment ready company - API activation',
                'status': 'PASSED',
                'error': f'API correctly allowed activation: {response.data}'
            })
            print(f"✓ Payment ready company can activate ads: {response.data}")
        else:
            self.test_results.append({
                'test': 'Payment ready company - API activation',
                'status': 'FAILED',
                'error': f'API blocked activation for payment ready company: {response.status_code} - {response.data}'
            })
            print(f"✗ API incorrectly blocked payment ready company: {response.data}")

    def test_utility_functions(self):
        """Test payment utility functions"""
        print("\n--- Testing Utility Functions ---")
        
        # Test with non-payment-ready company
        self.company.payment_ready = False
        self.company.save()
        
        try:
            validate_auction_publication(self.user)
            self.test_results.append({
                'test': 'Utility function validation',
                'status': 'FAILED',
                'error': 'validate_auction_publication allowed unpaid company'
            })
        except Exception as e:
            self.test_results.append({
                'test': 'Utility function validation',
                'status': 'PASSED', 
                'error': f'validate_auction_publication correctly blocked: {e}'
            })
            print(f"✓ Utility function correctly validated: {e}")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n--- Cleaning up test data ---")
        try:
            if hasattr(self, 'ad') and self.ad:
                self.ad.delete()
            if hasattr(self, 'company') and self.company:
                self.company.delete()  
            if hasattr(self, 'user') and self.user:
                self.user.delete()
            print("✓ Test data cleaned up")
        except Exception as e:
            print(f"Warning: Cleanup error: {e}")

    def run_all_tests(self):
        """Run complete test suite"""
        print("=== Payment Validation System Test Suite ===\n")
        
        try:
            self.create_test_data()
            self.test_model_validation()
            self.test_decorator_functionality()
            self.test_api_endpoint_protection()
            self.test_marketplace_filtering()
            self.test_payment_ready_company_flow()
            self.test_utility_functions()
        except Exception as e:
            print(f"Test execution error: {e}")
        finally:
            self.cleanup_test_data()
            
        self.print_results()

    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['status'] == 'PASSED')
        failed = sum(1 for result in self.test_results if result['status'] == 'FAILED') 
        errors = sum(1 for result in self.test_results if result['status'] == 'ERROR')
        
        print(f"Total tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print()
        
        for result in self.test_results:
            status_symbol = "✓" if result['status'] == 'PASSED' else "✗" if result['status'] == 'FAILED' else "⚠"
            print(f"{status_symbol} {result['test']}: {result['status']}")
            if result.get('error'):
                print(f"   Details: {result['error']}")
        
        print("\n" + "="*60)
        if failed == 0 and errors == 0:
            print("🎉 ALL TESTS PASSED! Payment validation system is working correctly.")
        else:
            print("⚠️  SOME TESTS FAILED. Please review the implementation.")


if __name__ == "__main__":
    tester = PaymentValidationTester()
    tester.run_all_tests()