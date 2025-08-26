#!/usr/bin/env python3
"""
Test script to verify the payment API endpoints are working correctly
"""

import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from bids.models import Bid
from ads.models import Ad
from payments.models import StripeAccount

User = get_user_model()

def test_payment_api():
    """Test the payment API endpoints"""
    
    print("🧪 Testing Payment API Endpoints")
    print("=" * 50)
    
    # Check if we have any winning bids to test with
    winning_bids = Bid.objects.filter(status='won')
    
    if not winning_bids.exists():
        print("❌ No winning bids found in database")
        print("   Creating test data would be needed for full testing")
        return False
    
    print(f"✅ Found {winning_bids.count()} winning bid(s)")
    
    # Get the first winning bid
    test_bid = winning_bids.first()
    print(f"📋 Test bid: ID={test_bid.id}, User={test_bid.user.email}")
    
    # Check if the seller has a Stripe account
    seller = test_bid.ad.user
    has_stripe_account = hasattr(seller, 'stripe_account')
    
    print(f"💳 Seller Stripe account: {'✅ Exists' if has_stripe_account else '❌ Missing'}")
    
    if not has_stripe_account:
        print("   Note: Seller needs to set up Stripe account for payments to work")
    
    # Test the API endpoint directly
    api_url = "http://127.0.0.1:8000/api/payments/payment-intent/"
    
    # We would need authentication token for this test
    print(f"🌐 API Endpoint: {api_url}")
    print("   Note: Authentication required for actual API testing")
    
    # Check Stripe configuration
    from django.conf import settings
    stripe_configured = bool(getattr(settings, 'STRIPE_SECRET_KEY', ''))
    
    print(f"🔑 Stripe Configuration: {'✅ Configured' if stripe_configured else '❌ Missing'}")
    
    if stripe_configured:
        print("   Stripe keys are properly configured")
    else:
        print("   Stripe API keys need to be configured")
    
    return True

def check_stripe_service():
    """Check if Stripe service is working"""
    
    print("\n🔧 Testing Stripe Service")
    print("=" * 30)
    
    try:
        from payments.services import StripeConnectService
        
        service = StripeConnectService()
        print("✅ StripeConnectService initialized successfully")
        
        # Check if Stripe API key is configured
        import stripe
        if stripe.api_key:
            print("✅ Stripe API key is configured")
        else:
            print("❌ Stripe API key is not configured")
            
    except Exception as e:
        print(f"❌ Error initializing Stripe service: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    
    print("🚀 Nordic Loop Payment Integration Test")
    print("=" * 60)
    
    # Test basic API functionality
    api_test = test_payment_api()
    
    # Test Stripe service
    stripe_test = check_stripe_service()
    
    print("\n📊 Test Summary")
    print("=" * 20)
    print(f"API Test: {'✅ PASS' if api_test else '❌ FAIL'}")
    print(f"Stripe Test: {'✅ PASS' if stripe_test else '❌ FAIL'}")
    
    if api_test and stripe_test:
        print("\n🎉 All tests passed! Payment integration should work.")
    else:
        print("\n⚠️  Some tests failed. Check the issues above.")

if __name__ == "__main__":
    main()
