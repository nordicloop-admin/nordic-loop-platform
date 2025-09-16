#!/usr/bin/env python3
"""
Test script for Stripe Connect integration
Tests the complete account creation and onboarding flow
"""

import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from company.models import Company
from company.stripe_service import StripeConnectService
from django.test import RequestFactory

User = get_user_model()

class StripeIntegrationTester:
    def __init__(self):
        self.factory = RequestFactory()
        
    def create_test_company(self):
        """Create a test company for testing"""
        print("Creating test company...")
        
        timestamp = int(time.time())
        username = f'stripetest{timestamp}'
        
        user = User.objects.create_user(
            username=username,
            email=f'{username}@test.com',
            password='testpass123'
        )
        
        company = Company.objects.create(
            official_name=f'Stripe Test Company {timestamp}',
            user=user,
            payment_ready=False,
        )
        
        user.company = company
        user.save()
        
        print(f"✓ Created user: {user.username}")
        print(f"✓ Created company: {company.official_name}")
        
        return user, company
    
    def test_account_creation(self, user, company):
        """Test Stripe Express account creation"""
        print("\n--- Testing Stripe Account Creation ---")
        
        success, message, account_id = StripeConnectService.create_express_account(
            company, user.email
        )
        
        if success:
            print(f"✓ Account created successfully: {account_id}")
            print(f"  Message: {message}")
            
            # Refresh company from DB
            company.refresh_from_db()
            print(f"  Company stripe_account_id: {company.stripe_account_id}")
            return True
        else:
            print(f"✗ Account creation failed: {message}")
            return False
    
    def test_account_status_check(self, company):
        """Test account status checking"""
        print("\n--- Testing Account Status Check ---")
        
        status_info = StripeConnectService.check_account_status(company)
        
        if status_info.get('exists'):
            print(f"✓ Account exists: {status_info.get('account_id')}")
            print(f"  Charges enabled: {status_info.get('charges_enabled')}")
            print(f"  Details submitted: {status_info.get('details_submitted')}")
            print(f"  Payouts enabled: {status_info.get('payouts_enabled')}")
            print(f"  Country: {status_info.get('country')}")
            print(f"  Requirements: {len(status_info.get('requirements', []))} items")
            
            capabilities = status_info.get('capabilities', {})
            for cap, status in capabilities.items():
                print(f"  Capability {cap}: {status}")
                
            # Check company status after update
            company.refresh_from_db()
            print(f"  Company payment_ready: {company.payment_ready}")
            print(f"  Company stripe_capabilities_complete: {company.stripe_capabilities_complete}")
            print(f"  Company stripe_onboarding_complete: {company.stripe_onboarding_complete}")
            
            return True
        else:
            error = status_info.get('error', 'Unknown error')
            print(f"✗ Failed to get account status: {error}")
            return False
    
    def test_onboarding_link_creation(self, company):
        """Test onboarding link creation"""
        print("\n--- Testing Onboarding Link Creation ---")
        
        # Create a mock request
        request = self.factory.get('/')
        request.META['HTTP_HOST'] = 'testserver'
        request.scheme = 'http'
        
        success, message, onboarding_url = StripeConnectService.create_account_link(
            company, request
        )
        
        if success:
            print(f"✓ Onboarding link created successfully")
            print(f"  URL: {onboarding_url}")
            print(f"  Message: {message}")
            return True
        else:
            print(f"✗ Failed to create onboarding link: {message}")
            return False
    
    def test_login_link_creation(self, company):
        """Test dashboard login link creation"""
        print("\n--- Testing Dashboard Login Link Creation ---")
        
        success, message, login_url = StripeConnectService.create_login_link(company)
        
        if success:
            print(f"✓ Dashboard login link created successfully")
            print(f"  URL: {login_url}")
            print(f"  Message: {message}")
            return True
        else:
            print(f"✗ Failed to create dashboard login link: {message}")
            return False
    
    def cleanup_test_data(self, user, company):
        """Clean up test data"""
        print("\n--- Cleaning up test data ---")
        
        try:
            # Note: In production, you might want to keep Stripe accounts
            # or properly close them through Stripe's API
            company.delete()
            user.delete()
            print("✓ Test data cleaned up")
        except Exception as e:
            print(f"Warning: Cleanup error: {e}")
    
    def run_complete_test(self):
        """Run the complete test suite"""
        print("=== Stripe Connect Integration Test Suite ===\n")
        
        try:
            # Step 1: Create test company
            user, company = self.create_test_company()
            
            # Step 2: Test account creation
            account_created = self.test_account_creation(user, company)
            if not account_created:
                print("\n❌ CRITICAL: Account creation failed. Cannot continue tests.")
                return False
            
            # Step 3: Test account status check
            status_checked = self.test_account_status_check(company)
            if not status_checked:
                print("\n⚠️  WARNING: Account status check failed")
            
            # Step 4: Test onboarding link creation
            onboarding_link_created = self.test_onboarding_link_creation(company)
            if not onboarding_link_created:
                print("\n⚠️  WARNING: Onboarding link creation failed")
            
            # Step 5: Test dashboard login link creation
            # This will likely fail since the account isn't fully onboarded
            print("\n--- Testing Dashboard Login Link (Expected to fail for new accounts) ---")
            login_link_created = self.test_login_link_creation(company)
            if not login_link_created:
                print("  Note: This is expected for newly created accounts that haven't completed onboarding")
            
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            
            tests = [
                ("Account Creation", account_created),
                ("Status Check", status_checked),
                ("Onboarding Link", onboarding_link_created),
            ]
            
            passed = sum(1 for _, result in tests if result)
            total = len(tests)
            
            print(f"Tests passed: {passed}/{total}")
            
            for test_name, result in tests:
                status_icon = "✓" if result else "✗"
                print(f"{status_icon} {test_name}")
            
            if passed == total:
                print("\n🎉 ALL CORE TESTS PASSED!")
                print("The Stripe Connect integration is working correctly.")
                print("\nNext steps:")
                print("1. Users can now create Stripe Express accounts")
                print("2. Users can access onboarding links to complete setup")
                print("3. Account status is properly tracked and updated")
                print("4. Users will be able to access dashboard once onboarding is complete")
            else:
                print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
            
            return passed == total
            
        except Exception as e:
            print(f"Test execution error: {e}")
            return False
        finally:
            if 'user' in locals() and 'company' in locals():
                self.cleanup_test_data(user, company)

if __name__ == "__main__":
    tester = StripeIntegrationTester()
    success = tester.run_complete_test()
    exit(0 if success else 1)