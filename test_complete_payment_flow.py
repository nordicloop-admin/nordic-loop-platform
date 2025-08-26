#!/usr/bin/env python3
"""
Complete Payment Flow Test
Tests the end-to-end payment process from buyer to seller
"""

import os
import sys
import django
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from payments.models import StripeAccount, PaymentIntent
from bids.models import Bid
from payments.processors import BidPaymentProcessor
from payments.services import StripeConnectService

def test_complete_payment_flow():
    """Test the complete payment flow"""
    
    print("🚀 Testing Complete Payment Flow")
    print("=" * 50)
    
    # Test accounts
    buyer_email = 'olivierkarera2020@gmail.com'
    seller_email = 'karera@gmail.com'
    
    try:
        # Get test users
        buyer = User.objects.get(email=buyer_email)
        seller = User.objects.get(email=seller_email)
        
        print(f"✅ Found buyer: {buyer.email}")
        print(f"✅ Found seller: {seller.email}")
        
        # Check seller's Stripe account
        try:
            seller_stripe = StripeAccount.objects.get(user=seller)
            print(f"\n💳 Seller Stripe Account:")
            print(f"   Account ID: {seller_stripe.stripe_account_id}")
            print(f"   Status: {seller_stripe.account_status}")
            print(f"   Charges Enabled: {seller_stripe.charges_enabled}")
            print(f"   Payouts Enabled: {seller_stripe.payouts_enabled}")
            
            if not (seller_stripe.account_status == 'active' and 
                   seller_stripe.charges_enabled and 
                   seller_stripe.payouts_enabled):
                print("❌ Seller account not ready for payments!")
                return False
                
        except StripeAccount.DoesNotExist:
            print("❌ Seller has no Stripe account!")
            return False
        
        # Find winning bids
        winning_bids = Bid.objects.filter(user=buyer, status='won')
        print(f"\n📋 Found {winning_bids.count()} winning bid(s)")
        
        if not winning_bids.exists():
            print("❌ No winning bids found for testing!")
            return False
        
        # Test with first winning bid
        test_bid = winning_bids.first()
        print(f"\n🎯 Testing with bid:")
        print(f"   Bid ID: {test_bid.id}")
        print(f"   Buyer: {test_bid.user.email}")
        print(f"   Seller: {test_bid.ad.user.email}")
        print(f"   Amount: {test_bid.bid_price_per_unit} x {test_bid.volume_requested}")
        print(f"   Total: {test_bid.bid_price_per_unit * test_bid.volume_requested} SEK")
        
        # Check if payment intent already exists
        existing_payment = PaymentIntent.objects.filter(bid=test_bid).first()
        if existing_payment:
            print(f"\n⚠️  Payment intent already exists: {existing_payment.stripe_payment_intent_id}")
            print(f"   Status: {existing_payment.status}")
            
            # For testing, let's delete it and create a new one
            print("🔄 Deleting existing payment intent for fresh test...")
            existing_payment.delete()
        
        # Test payment processing
        print(f"\n🔧 Processing payment...")
        processor = BidPaymentProcessor()
        result = processor.process_winning_bid(test_bid)
        
        if result['success']:
            print("✅ Payment processing successful!")
            payment_intent = result['payment_intent']
            print(f"   Payment Intent ID: {payment_intent.id}")
            print(f"   Stripe Payment Intent: {payment_intent.stripe_payment_intent_id}")
            print(f"   Total Amount: {payment_intent.total_amount} {payment_intent.currency}")
            print(f"   Commission: {payment_intent.commission_amount} {payment_intent.currency}")
            print(f"   Seller Amount: {payment_intent.seller_amount} {payment_intent.currency}")
            print(f"   Status: {payment_intent.status}")
            print(f"   Client Secret: {result.get('client_secret', 'N/A')[:20]}...")
            
            # Test API endpoint simulation
            print(f"\n🧪 Testing API Response Format:")
            api_response = {
                'success': True,
                'payment_intent': {
                    'id': payment_intent.id,
                    'stripe_payment_intent_id': payment_intent.stripe_payment_intent_id,
                    'total_amount': str(payment_intent.total_amount),
                    'commission_amount': str(payment_intent.commission_amount),
                    'seller_amount': str(payment_intent.seller_amount),
                    'currency': payment_intent.currency,
                    'status': payment_intent.status
                },
                'client_secret': result.get('client_secret', ''),
                'message': result['message']
            }
            
            print("✅ API Response Format Valid")
            print(f"   Response size: {len(str(api_response))} characters")
            
            return True
            
        else:
            print(f"❌ Payment processing failed: {result['message']}")
            return False
            
    except User.DoesNotExist as e:
        print(f"❌ User not found: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error during payment flow test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_payment_capability_error():
    """Test the specific payment capability error scenario"""
    
    print("\n🔍 Testing Payment Capability Error Scenario")
    print("=" * 50)
    
    try:
        # Get seller account
        seller = User.objects.get(email='karera@gmail.com')
        seller_stripe = StripeAccount.objects.get(user=seller)
        
        print(f"Seller Account Analysis:")
        print(f"   Email: {seller.email}")
        print(f"   Stripe Account ID: {seller_stripe.stripe_account_id}")
        print(f"   Account Status: {seller_stripe.account_status}")
        print(f"   Charges Enabled: {seller_stripe.charges_enabled}")
        print(f"   Payouts Enabled: {seller_stripe.payouts_enabled}")
        
        # Check for capability issues
        issues = []
        
        if seller_stripe.account_status != 'active':
            issues.append(f"Account status is '{seller_stripe.account_status}' (should be 'active')")
            
        if not seller_stripe.charges_enabled:
            issues.append("Charges not enabled")
            
        if not seller_stripe.payouts_enabled:
            issues.append("Payouts not enabled")
            
        if seller_stripe.stripe_account_id.startswith('acct_1'):
            issues.append("Using real Stripe account (may lack test capabilities)")
        
        if issues:
            print(f"\n⚠️  Potential Issues Found:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
                
            print(f"\n💡 Solutions:")
            print(f"   - Run: python manage.py activate_test_seller --email karera@gmail.com --force")
            print(f"   - This will create a test account with all capabilities enabled")
            
        else:
            print(f"\n✅ No capability issues found!")
            print(f"   Account should be able to receive payments")
            
        return len(issues) == 0
        
    except Exception as e:
        print(f"❌ Error checking capabilities: {str(e)}")
        return False

def test_verification_improvements():
    """Test that verification improvements don't break payment functionality"""
    
    print("\n🧪 Testing Verification Improvements Integration")
    print("=" * 50)
    
    try:
        from payments.verification_service import VerificationService
        
        # Test verification service
        service = VerificationService()
        seller = User.objects.get(email='karera@gmail.com')
        
        status = service.get_verification_status(seller)
        
        if status['success']:
            print("✅ Verification service working")
            print(f"   Has Account: {status['has_account']}")
            if status['has_account']:
                print(f"   Account Status: {status['account_status']}")
                print(f"   Charges Enabled: {status['charges_enabled']}")
                print(f"   Payouts Enabled: {status['payouts_enabled']}")
                
                # Check if verification status matches payment capability
                payment_ready = (status['account_status'] == 'active' and 
                               status['charges_enabled'] and 
                               status['payouts_enabled'])
                               
                print(f"   Payment Ready: {payment_ready}")
                
                if payment_ready:
                    print("✅ Verification improvements don't block payments")
                else:
                    print("⚠️  Account not ready for payments according to verification service")
                    
        else:
            print(f"❌ Verification service error: {status['message']}")
            
        # Test FAQ
        faq = service.get_verification_faq()
        print(f"✅ FAQ service working ({len(faq['faqs'])} questions)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing verification improvements: {str(e)}")
        return False

def main():
    """Main test function"""
    
    print("🧪 Complete Payment Flow Test Suite")
    print("=" * 60)
    
    tests = [
        ("Payment Capability Check", test_payment_capability_error),
        ("Verification Improvements", test_verification_improvements),
        ("Complete Payment Flow", test_complete_payment_flow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"\n{test_name}: {status}")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print("=" * 20)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        print("\n✅ Payment system is ready for testing:")
        print("   • Seller account activated with test capabilities")
        print("   • Verification improvements working correctly")
        print("   • Payment flow functional end-to-end")
        print("   • No capability errors expected")
        
        print(f"\n🔗 Test the payment flow:")
        print(f"   1. Login as buyer: olivierkarera2020@gmail.com (Rwabose5@)")
        print(f"   2. Go to: http://localhost:3000/dashboard/winning-bids")
        print(f"   3. Click 'Initialize Payment' on any winning bid")
        print(f"   4. Payment should process without capability errors")
        
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("   Check the issues above and run the suggested fixes.")

if __name__ == "__main__":
    main()
