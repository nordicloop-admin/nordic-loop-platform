#!/usr/bin/env python
"""
Payment System Validation Report

This script generates a comprehensive validation report for the Nordic Loop payment system
after implementing the automatic payment completion workflow fixes.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from payments.models import PaymentIntent, Transaction, StripeAccount
from bids.models import Bid
from notifications.models import Notification

User = get_user_model()

def generate_validation_report():
    """Generate comprehensive validation report"""
    
    print("🎯 NORDIC LOOP PAYMENT SYSTEM VALIDATION REPORT")
    print("=" * 60)
    print(f"Generated: {datetime.now()}")
    print(f"Environment: {getattr(settings, 'DJANGO_ENV', 'development')}")
    
    # 1. WEBHOOK CONFIGURATION
    print("\n📡 WEBHOOK CONFIGURATION")
    print("-" * 25)
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    stripe_secret = getattr(settings, 'STRIPE_SECRET_KEY', '')
    
    webhook_configured = webhook_secret and webhook_secret != 'whsec_your_webhook_secret_here'
    print(f"Webhook Secret: {'✅ Configured' if webhook_configured else '❌ Missing/Placeholder'}")
    print(f"Stripe API Key: {'✅ Configured' if stripe_secret else '❌ Missing'}")
    print(f"Development Bypass: {'✅ Active' if webhook_secret.startswith('whsec_test_') else '❌ Not Active'}")
    
    # 2. PAYMENT SYSTEM STATE
    print("\n💳 PAYMENT SYSTEM STATE")
    print("-" * 25)
    
    total_payments = PaymentIntent.objects.count()
    succeeded_payments = PaymentIntent.objects.filter(status='succeeded').count()
    stuck_payments = PaymentIntent.objects.filter(status='requires_payment_method').count()
    total_transactions = Transaction.objects.count()
    
    print(f"Total PaymentIntents: {total_payments}")
    print(f"Succeeded Payments: {succeeded_payments}")
    print(f"Stuck Payments: {stuck_payments}")
    print(f"Total Transactions: {total_transactions}")
    print(f"Success Rate: {(succeeded_payments/total_payments*100):.1f}%" if total_payments > 0 else "N/A")
    
    # 3. BID STATUS CONSISTENCY
    print("\n🎯 BID STATUS CONSISTENCY")
    print("-" * 25)
    
    paid_bids = Bid.objects.filter(status='paid').count()
    won_bids = Bid.objects.filter(status='won').count()
    
    print(f"Paid Bids: {paid_bids}")
    print(f"Won Bids (Unpaid): {won_bids}")
    
    # Check consistency between PaymentIntents and Bid status
    succeeded_payment_bids = PaymentIntent.objects.filter(status='succeeded').values_list('bid_id', flat=True)
    inconsistent_bids = 0
    
    for bid_id in succeeded_payment_bids:
        bid = Bid.objects.get(id=bid_id)
        if bid.status != 'paid':
            inconsistent_bids += 1
    
    print(f"Bid Status Consistency: {'✅ All Consistent' if inconsistent_bids == 0 else f'❌ {inconsistent_bids} Inconsistent'}")
    
    # 4. TRANSACTION COMPLETENESS
    print("\n💰 TRANSACTION COMPLETENESS")
    print("-" * 28)
    
    commission_transactions = Transaction.objects.filter(transaction_type='commission').count()
    payout_transactions = Transaction.objects.filter(transaction_type='payout').count()
    
    print(f"Commission Transactions: {commission_transactions}")
    print(f"Payout Transactions: {payout_transactions}")
    print(f"Transaction Pairs: {'✅ Complete' if commission_transactions == payout_transactions else '❌ Incomplete'}")
    
    # Expected: Each succeeded payment should have 2 transactions (commission + payout)
    expected_transactions = succeeded_payments * 2
    print(f"Expected Transactions: {expected_transactions}")
    print(f"Actual Transactions: {total_transactions}")
    print(f"Transaction Completeness: {'✅ Complete' if total_transactions == expected_transactions else '❌ Incomplete'}")
    
    # 5. USER DASHBOARD DATA
    print("\n👥 USER DASHBOARD DATA")
    print("-" * 21)
    
    try:
        buyer = User.objects.get(email='olivierkarera2020@gmail.com')
        seller = User.objects.get(email='karera@gmail.com')
        
        buyer_payments = PaymentIntent.objects.filter(buyer=buyer, status='succeeded').count()
        seller_payments = PaymentIntent.objects.filter(seller=seller, status='succeeded').count()
        
        buyer_transactions = Transaction.objects.filter(from_user=buyer).count()
        seller_transactions = Transaction.objects.filter(to_user=seller).count()
        
        print(f"Buyer ({buyer.email}):")
        print(f"  - Completed Payments: {buyer_payments}")
        print(f"  - Transactions: {buyer_transactions}")
        
        print(f"Seller ({seller.email}):")
        print(f"  - Received Payments: {seller_payments}")
        print(f"  - Transactions: {seller_transactions}")
        
        dashboard_data_complete = buyer_payments > 0 and seller_payments > 0
        print(f"Dashboard Data: {'✅ Available' if dashboard_data_complete else '❌ Missing'}")
        
    except User.DoesNotExist:
        print("❌ Test users not found")
        dashboard_data_complete = False
    
    # 6. NOTIFICATION SYSTEM
    print("\n🔔 NOTIFICATION SYSTEM")
    print("-" * 20)
    
    payment_notifications = Notification.objects.filter(type='payment').count()
    recent_notifications = Notification.objects.filter(
        type='payment',
        date__gte=datetime.now().replace(hour=0, minute=0, second=0)
    ).count()
    
    print(f"Payment Notifications: {payment_notifications}")
    print(f"Recent Notifications: {recent_notifications}")
    print(f"Notification System: {'✅ Active' if payment_notifications > 0 else '⚠️  No Notifications'}")
    
    # 7. STRIPE ACCOUNT STATUS
    print("\n🏦 STRIPE ACCOUNT STATUS")
    print("-" * 23)
    
    active_accounts = StripeAccount.objects.filter(account_status='active').count()
    total_accounts = StripeAccount.objects.count()
    
    print(f"Total Stripe Accounts: {total_accounts}")
    print(f"Active Accounts: {active_accounts}")
    print(f"Account Setup: {'✅ Ready' if active_accounts > 0 else '❌ No Active Accounts'}")
    
    # 8. SYSTEM HEALTH SUMMARY
    print("\n🏥 SYSTEM HEALTH SUMMARY")
    print("-" * 25)
    
    health_checks = [
        ("Webhook Configuration", webhook_configured),
        ("Payment Completion", stuck_payments == 0),
        ("Bid Status Consistency", inconsistent_bids == 0),
        ("Transaction Completeness", total_transactions == expected_transactions),
        ("Dashboard Data", dashboard_data_complete),
        ("Stripe Accounts", active_accounts > 0)
    ]
    
    passed_checks = sum(1 for _, status in health_checks if status)
    total_checks = len(health_checks)
    
    for check_name, status in health_checks:
        print(f"{check_name}: {'✅ PASS' if status else '❌ FAIL'}")
    
    print(f"\nOverall Health: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("🎉 SYSTEM FULLY OPERATIONAL")
        print("   All payment workflows are functioning correctly")
    elif passed_checks >= total_checks * 0.8:
        print("⚠️  SYSTEM MOSTLY OPERATIONAL")
        print("   Minor issues detected, but core functionality works")
    else:
        print("❌ SYSTEM NEEDS ATTENTION")
        print("   Critical issues detected, immediate action required")
    
    # 9. RECOMMENDATIONS
    print("\n📋 RECOMMENDATIONS")
    print("-" * 17)
    
    if not webhook_configured:
        print("• Configure proper Stripe webhook secret for production")
    
    if stuck_payments > 0:
        print("• Run webhook simulation to fix stuck payments")
    
    if inconsistent_bids > 0:
        print("• Update bid statuses for completed payments")
    
    if total_transactions != expected_transactions:
        print("• Check transaction creation in PaymentCompletionService")
    
    if active_accounts == 0:
        print("• Set up Stripe accounts for sellers")
    
    print("\n🚀 NEXT STEPS FOR PRODUCTION:")
    print("1. Set up real Stripe webhook endpoint with HTTPS")
    print("2. Configure production webhook secret")
    print("3. Test end-to-end payment flow")
    print("4. Monitor webhook delivery in Stripe Dashboard")
    print("5. Set up payment monitoring and alerts")
    
    return passed_checks == total_checks

if __name__ == "__main__":
    system_healthy = generate_validation_report()
    sys.exit(0 if system_healthy else 1)
