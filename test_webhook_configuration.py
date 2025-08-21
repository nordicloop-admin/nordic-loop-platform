#!/usr/bin/env python
"""
Webhook Configuration Test Script

This script helps test and configure Stripe webhooks for the Nordic Loop payment system.
It provides utilities to:
1. Test webhook endpoint accessibility
2. Validate webhook secret configuration
3. Simulate webhook events for testing
4. Check payment completion workflow
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from payments.models import PaymentIntent, Transaction
from payments.webhooks import handle_payment_intent_succeeded
import stripe

def test_webhook_configuration():
    """Test current webhook configuration"""
    print("🔧 Testing Webhook Configuration")
    print("=" * 40)
    
    # Check environment variables
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    stripe_secret = getattr(settings, 'STRIPE_SECRET_KEY', '')
    
    print(f"Webhook Secret: {'✅ Configured' if webhook_secret and webhook_secret != 'whsec_your_webhook_secret_here' else '❌ Missing/Placeholder'}")
    print(f"Stripe Secret Key: {'✅ Configured' if stripe_secret else '❌ Missing'}")
    
    if webhook_secret == 'whsec_your_webhook_secret_here':
        print("\n⚠️  WEBHOOK SECRET IS PLACEHOLDER!")
        print("   This is why automatic payment completion is failing.")
        print("   To fix this:")
        print("   1. Go to Stripe Dashboard > Developers > Webhooks")
        print("   2. Create/edit webhook endpoint")
        print("   3. Copy the webhook signing secret")
        print("   4. Update STRIPE_WEBHOOK_SECRET in .env file")
        return False
    
    return True

def test_webhook_endpoint():
    """Test if webhook endpoint is accessible"""
    print("\n🌐 Testing Webhook Endpoint")
    print("=" * 30)
    
    # Try to access the webhook endpoint
    try:
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        # Assume backend is on port 8000 if frontend is on 3000
        backend_url = frontend_url.replace(':3000', ':8000').replace('https://', 'http://')
        webhook_url = f"{backend_url}/api/payments/webhooks/stripe/"
        
        print(f"Testing webhook URL: {webhook_url}")
        
        # Make a test request (this will fail signature verification, but endpoint should respond)
        response = requests.post(webhook_url, 
                               data='test', 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code in [400, 401]:  # Expected for invalid signature
            print("✅ Webhook endpoint is accessible")
            print(f"   Response: {response.status_code} - {response.text[:100]}")
            return True
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach webhook endpoint: {e}")
        return False

def simulate_payment_success():
    """Simulate a successful payment webhook for testing"""
    print("\n🧪 Simulating Payment Success Webhook")
    print("=" * 40)
    
    # Find a payment intent that's stuck
    stuck_payments = PaymentIntent.objects.filter(status='requires_payment_method')
    
    if not stuck_payments.exists():
        print("❌ No stuck payment intents found to test with")
        return False
    
    payment_intent = stuck_payments.first()
    print(f"Testing with PaymentIntent: {payment_intent.id}")
    print(f"Stripe Payment Intent ID: {payment_intent.stripe_payment_intent_id}")
    print(f"Current Status: {payment_intent.status}")
    
    # Create mock webhook data
    mock_webhook_data = {
        'id': payment_intent.stripe_payment_intent_id,
        'status': 'succeeded',
        'amount': int(payment_intent.total_amount * 100),  # Convert to cents
        'currency': payment_intent.currency.lower(),
        'metadata': {
            'bid_id': str(payment_intent.bid.id),
            'buyer_id': str(payment_intent.buyer.id),
            'seller_id': str(payment_intent.seller.id)
        }
    }
    
    print(f"\n📤 Simulating webhook call...")
    
    try:
        # Call the webhook handler directly
        handle_payment_intent_succeeded(mock_webhook_data)
        
        # Check if it worked
        payment_intent.refresh_from_db()
        transactions = Transaction.objects.filter(payment_intent=payment_intent)
        
        print(f"✅ Webhook simulation completed")
        print(f"   New Status: {payment_intent.status}")
        print(f"   Transactions Created: {transactions.count()}")
        
        for transaction in transactions:
            print(f"   - {transaction.transaction_type}: {transaction.amount} {transaction.currency} ({transaction.status})")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook simulation failed: {e}")
        return False

def check_payment_system_state():
    """Check current state of payment system"""
    print("\n📊 Payment System State")
    print("=" * 25)
    
    total_payments = PaymentIntent.objects.count()
    succeeded_payments = PaymentIntent.objects.filter(status='succeeded').count()
    stuck_payments = PaymentIntent.objects.filter(status='requires_payment_method').count()
    total_transactions = Transaction.objects.count()
    
    print(f"Total PaymentIntents: {total_payments}")
    print(f"Succeeded: {succeeded_payments}")
    print(f"Stuck (requires_payment_method): {stuck_payments}")
    print(f"Total Transactions: {total_transactions}")
    
    if stuck_payments > 0:
        print(f"\n⚠️  {stuck_payments} payments are stuck and need webhook completion")
        
        # Show details of stuck payments
        stuck = PaymentIntent.objects.filter(status='requires_payment_method')[:3]
        for pi in stuck:
            print(f"   - {pi.id}: Bid {pi.bid_id}, Amount {pi.total_amount}")
    
    return stuck_payments == 0

def main():
    """Main test function"""
    print("🚀 Nordic Loop Webhook Configuration Test")
    print("=" * 45)
    print(f"Timestamp: {datetime.now()}")
    
    # Run all tests
    webhook_configured = test_webhook_configuration()
    endpoint_accessible = test_webhook_endpoint()
    system_healthy = check_payment_system_state()
    
    print("\n" + "=" * 45)
    print("📋 SUMMARY")
    print("=" * 45)
    
    if webhook_configured and endpoint_accessible:
        print("✅ Webhook system appears to be configured correctly")
        
        if not system_healthy:
            print("🔧 Running webhook simulation to fix stuck payments...")
            simulate_payment_success()
    else:
        print("❌ Webhook system needs configuration")
        print("\n🔧 NEXT STEPS:")
        print("1. Configure proper webhook secret in Stripe Dashboard")
        print("2. Update .env file with real webhook secret")
        print("3. Restart Django server")
        print("4. Test payment flow")
    
    print("\n🎯 For production deployment:")
    print("   - Set up webhook endpoint in Stripe Dashboard")
    print("   - Use HTTPS URL for webhook endpoint")
    print("   - Configure proper webhook secret")
    print("   - Monitor webhook delivery in Stripe Dashboard")

if __name__ == "__main__":
    main()
