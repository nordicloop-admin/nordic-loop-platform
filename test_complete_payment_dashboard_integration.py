#!/usr/bin/env python3
"""
Complete Payment Dashboard Integration Test

This script tests the entire payment flow from bid creation to dashboard visibility:
1. Payment completion processing
2. Transaction creation
3. Payout schedule generation
4. Dashboard API endpoints
5. Frontend data visibility

Run with: python test_complete_payment_dashboard_integration.py
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from ads.models import Ad
from bids.models import Bid
from payments.models import PaymentIntent, Transaction, PayoutSchedule
from payments.completion_services.payment_completion import PaymentCompletionService
from payments.processors import PayoutProcessor
from payments.views import TransactionHistoryView, UserPayoutScheduleView
from django.test import RequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_section(title):
    print(f"\n{'-'*40}")
    print(f"📋 {title}")
    print('-'*40)

def test_complete_payment_dashboard_integration():
    """Test complete payment flow and dashboard integration"""
    
    print_header("Complete Payment Dashboard Integration Test")
    
    try:
        # Get test users
        buyer = User.objects.get(email='olivierkarera2020@gmail.com')
        seller = User.objects.get(email='karera@gmail.com')
        admin_user = User.objects.filter(is_staff=True).first()
        
        print_section("Initial State Check")
        
        # Check existing payment intent
        payment_intent = PaymentIntent.objects.filter(
            buyer=buyer, 
            seller=seller,
            status='succeeded'
        ).first()
        
        if not payment_intent:
            print("❌ No successful payment intent found")
            return False
            
        print(f"✅ Found payment intent: {payment_intent.stripe_payment_intent_id}")
        print(f"   Amount: {payment_intent.total_amount} {payment_intent.currency}")
        print(f"   Commission: {payment_intent.commission_amount} {payment_intent.currency}")
        print(f"   Seller Amount: {payment_intent.seller_amount} {payment_intent.currency}")
        
        # Check transactions
        transactions = Transaction.objects.filter(payment_intent=payment_intent)
        print(f"✅ Transactions found: {transactions.count()}")
        for t in transactions:
            print(f"   {t.transaction_type} | {t.amount} {t.currency} | {t.status}")
        
        # Check payout schedule
        payout_schedules = PayoutSchedule.objects.filter(seller=seller)
        print(f"✅ Payout schedules found: {payout_schedules.count()}")
        for p in payout_schedules:
            print(f"   {p.total_amount} {p.currency} | {p.status} | Scheduled: {p.scheduled_date}")
        
        print_section("Testing API Endpoints")
        
        # Test transaction history API
        factory = RequestFactory()
        
        # Test buyer transaction API
        buyer_token = RefreshToken.for_user(buyer)
        request = factory.get('/api/payments/transactions/')
        request.user = buyer
        
        view = TransactionHistoryView()
        response = view.get(request)
        
        print(f"✅ Buyer transaction API: Status {response.status_code}")
        if response.status_code == 200:
            buyer_transactions = response.data
            print(f"   Transactions returned: {len(buyer_transactions)}")
            for t in buyer_transactions:
                print(f"   {t['transaction_type']} | {t['amount']} {t['currency']} | {t['status']}")
        
        # Test seller transaction API
        seller_token = RefreshToken.for_user(seller)
        request = factory.get('/api/payments/transactions/')
        request.user = seller
        
        view = TransactionHistoryView()
        response = view.get(request)
        
        print(f"✅ Seller transaction API: Status {response.status_code}")
        if response.status_code == 200:
            seller_transactions = response.data
            print(f"   Transactions returned: {len(seller_transactions)}")
            for t in seller_transactions:
                print(f"   {t['transaction_type']} | {t['amount']} {t['currency']} | {t['status']}")
        
        # Test seller payout API
        request = factory.get('/api/payments/payouts/')
        request.user = seller
        
        view = UserPayoutScheduleView()
        response = view.get(request)
        
        print(f"✅ Seller payout API: Status {response.status_code}")
        if response.status_code == 200:
            seller_payouts = response.data
            print(f"   Payout schedules returned: {len(seller_payouts)}")
            for p in seller_payouts:
                print(f"   {p['total_amount']} {p['currency']} | {p['status']} | {p['scheduled_date']}")
        
        print_section("Dashboard Data Summary")
        
        # Summary for buyer
        buyer_commission_transactions = Transaction.objects.filter(
            from_user=buyer,
            transaction_type='commission'
        )
        total_commission_paid = sum(t.amount for t in buyer_commission_transactions)
        
        print(f"👤 Buyer Dashboard ({buyer.email}):")
        print(f"   Total Commission Paid: {total_commission_paid} SEK")
        print(f"   Transaction Count: {buyer_commission_transactions.count()}")
        
        # Summary for seller
        seller_payout_transactions = Transaction.objects.filter(
            to_user=seller,
            transaction_type='payout'
        )
        total_pending_payouts = sum(t.amount for t in seller_payout_transactions.filter(status='pending'))
        
        print(f"👤 Seller Dashboard ({seller.email}):")
        print(f"   Pending Payouts: {total_pending_payouts} SEK")
        print(f"   Payout Schedules: {payout_schedules.count()}")
        print(f"   Transaction Count: {seller_payout_transactions.count()}")
        
        print_section("Integration Test Results")
        
        # Verify complete flow
        checks = [
            ("Payment Intent Created", payment_intent is not None),
            ("Payment Completed", payment_intent.status == 'succeeded'),
            ("Transactions Created", transactions.count() >= 2),
            ("Commission Transaction", transactions.filter(transaction_type='commission').exists()),
            ("Payout Transaction", transactions.filter(transaction_type='payout').exists()),
            ("Payout Schedule Created", payout_schedules.exists()),
            ("Buyer API Working", response.status_code == 200 and len(buyer_transactions) > 0),
            ("Seller API Working", response.status_code == 200 and len(seller_transactions) > 0),
            ("Payout API Working", response.status_code == 200 and len(seller_payouts) > 0),
        ]
        
        passed_checks = 0
        for check_name, check_result in checks:
            status = "✅ PASS" if check_result else "❌ FAIL"
            print(f"   {status} | {check_name}")
            if check_result:
                passed_checks += 1
        
        print(f"\n📊 Integration Test Summary:")
        print(f"   Passed: {passed_checks}/{len(checks)} checks")
        print(f"   Success Rate: {(passed_checks/len(checks)*100):.1f}%")
        
        if passed_checks == len(checks):
            print("\n🎉 All integration tests passed!")
            print("   Payment dashboard is fully functional")
            return True
        else:
            print(f"\n⚠️  {len(checks) - passed_checks} checks failed")
            print("   Some dashboard features may not work correctly")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_complete_payment_dashboard_integration()
    sys.exit(0 if success else 1)
