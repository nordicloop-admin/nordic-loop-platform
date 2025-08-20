#!/usr/bin/env python3
"""
Payment Flow Demo Script

This script demonstrates the complete auction winner payment flow by:
1. Creating sample auctions and bids
2. Testing auction closure with winner notifications
3. Testing payment processing and completion
4. Verifying all notifications are sent correctly

Run this script to validate the payment integration works as expected.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from ads.models import Ad
from ads.auction_services.auction_completion import AuctionCompletionService
from bids.models import Bid
from bids.services import BidService
from notifications.models import Notification
from payments.models import PaymentIntent, StripeAccount
from payments.processors import BidPaymentProcessor
from payments.completion_services.payment_completion import PaymentCompletionService
from categories.models import Category, Subcategory
from locations.models import Location

User = get_user_model()


def create_test_data():
    """Create test users, auction, and bids for payment flow testing"""
    print("🔧 Creating test data for payment flow...")
    
    # Create test users
    seller, _ = User.objects.get_or_create(
        username='payment_seller@test.com',
        defaults={
            'email': 'payment_seller@test.com',
            'first_name': 'Payment',
            'last_name': 'Seller'
        }
    )
    
    buyer, _ = User.objects.get_or_create(
        username='payment_buyer@test.com',
        defaults={
            'email': 'payment_buyer@test.com',
            'first_name': 'Payment',
            'last_name': 'Buyer'
        }
    )
    
    # Create seller's Stripe account (mock)
    stripe_account, _ = StripeAccount.objects.get_or_create(
        user=seller,
        defaults={
            'stripe_account_id': 'acct_test_payment_seller',
            'account_status': 'active',
            'charges_enabled': True,
            'payouts_enabled': True,
            'bank_account_last4': '1234',
            'bank_name': 'Test Bank',
            'bank_country': 'SE'
        }
    )
    
    # Create category and location
    category, _ = Category.objects.get_or_create(name='Payment Test Materials')
    subcategory, _ = Subcategory.objects.get_or_create(
        name='Payment Test Plastic',
        defaults={'category': category}
    )
    location, _ = Location.objects.get_or_create(
        country='Payment Test Country',
        defaults={'city': 'Payment Test City'}
    )
    
    # Create expired auction for payment flow test
    auction = Ad.objects.create(
        user=seller,
        category=category,
        subcategory=subcategory,
        location=location,
        title='Payment Flow Test Auction',
        description='This auction is for testing the complete payment flow',
        available_quantity=Decimal('100.00'),
        unit_of_measurement='tons',
        starting_bid_price=Decimal('50.00'),
        currency='EUR',
        auction_duration=7,
        is_complete=True,
        is_active=True,
        auction_start_date=timezone.now() - timedelta(days=8),
        auction_end_date=timezone.now() - timedelta(minutes=10)  # Expired 10 minutes ago
    )
    
    # Create winning bid
    winning_bid = Bid.objects.create(
        user=buyer,
        ad=auction,
        bid_price_per_unit=Decimal('85.00'),
        volume_requested=Decimal('50.00'),
        status='active'
    )
    
    print(f"✅ Created test data:")
    print(f"   - Seller: {seller.email} (Stripe Account: {stripe_account.stripe_account_id})")
    print(f"   - Buyer: {buyer.email}")
    print(f"   - Auction: {auction.title} (ID: {auction.id})")
    print(f"   - Winning bid: {winning_bid.bid_price_per_unit} EUR/ton for {winning_bid.volume_requested} tons")
    print(f"   - Total value: {winning_bid.total_bid_value} EUR")
    
    return {
        'seller': seller,
        'buyer': buyer,
        'auction': auction,
        'winning_bid': winning_bid,
        'stripe_account': stripe_account
    }


def test_auction_closure_with_notifications(test_data):
    """Test auction closure and winner notification"""
    print("\n🏆 Testing auction closure with winner notifications...")
    
    auction_service = AuctionCompletionService()
    
    # Close the expired auction
    result = auction_service.close_auction_with_notifications(test_data['auction'])
    
    print(f"   Closure result: {result}")
    
    if result['success'] and result['has_winner']:
        print(f"   ✅ Auction closed successfully")
        print(f"   Winner: {result['winner_email']}")
        print(f"   Winning price: {result['winning_price']} {result['currency']}")
        
        # Check winner notification was sent
        notifications = Notification.objects.filter(
            user=test_data['buyer'],
            type='auction',
            metadata__action_type='auction_won'
        )
        
        if notifications.exists():
            notification = notifications.first()
            print(f"   ✅ Winner notification sent: '{notification.title}'")
            print(f"   Action URL: {notification.action_url}")
            return True
        else:
            print(f"   ❌ Winner notification not found")
            return False
    else:
        print(f"   ❌ Auction closure failed: {result.get('message', 'Unknown error')}")
        return False


def test_payment_intent_creation(test_data):
    """Test payment intent creation for winning bid"""
    print("\n💳 Testing payment intent creation...")
    
    # Update bid status to 'won' first
    winning_bid = test_data['winning_bid']
    winning_bid.status = 'won'
    winning_bid.save()
    
    processor = BidPaymentProcessor()
    result = processor.process_winning_bid(winning_bid)
    
    print(f"   Payment intent creation result: {result}")
    
    if result['success']:
        payment_intent = result['payment_intent']
        print(f"   ✅ Payment intent created successfully")
        print(f"   Payment Intent ID: {payment_intent.id}")
        print(f"   Stripe Payment Intent ID: {payment_intent.stripe_payment_intent_id}")
        print(f"   Total amount: {payment_intent.total_amount} {payment_intent.currency}")
        print(f"   Commission: {payment_intent.commission_amount} {payment_intent.currency}")
        print(f"   Seller amount: {payment_intent.seller_amount} {payment_intent.currency}")
        
        test_data['payment_intent'] = payment_intent
        return True
    else:
        print(f"   ❌ Payment intent creation failed: {result['message']}")
        return False


def test_payment_completion(test_data):
    """Test payment completion and notifications"""
    print("\n✅ Testing payment completion...")
    
    if 'payment_intent' not in test_data:
        print("   ❌ No payment intent available for testing")
        return False
    
    payment_intent = test_data['payment_intent']
    
    # Simulate successful payment by updating status
    payment_intent.status = 'succeeded'
    payment_intent.confirmed_at = timezone.now()
    payment_intent.save()
    
    # Process payment completion
    completion_service = PaymentCompletionService()
    result = completion_service.process_payment_completion(payment_intent)
    
    print(f"   Payment completion result: {result}")
    
    if result['success']:
        print(f"   ✅ Payment completion processed successfully")
        print(f"   Transaction ID: {result['transaction_id']}")
        print(f"   Buyer notification sent: {result['buyer_notification_sent']}")
        print(f"   Seller notification sent: {result['seller_notification_sent']}")
        
        # Check buyer confirmation notification
        buyer_notifications = Notification.objects.filter(
            user=test_data['buyer'],
            type='payment',
            metadata__action_type='payment_confirmation'
        )
        
        # Check seller payment notification
        seller_notifications = Notification.objects.filter(
            user=test_data['seller'],
            type='payment',
            metadata__action_type='payment_received'
        )
        
        print(f"   Buyer notifications found: {buyer_notifications.count()}")
        print(f"   Seller notifications found: {seller_notifications.count()}")
        
        # Check bid status update
        winning_bid = test_data['winning_bid']
        winning_bid.refresh_from_db()
        print(f"   Bid status after payment: {winning_bid.status}")
        
        return True
    else:
        print(f"   ❌ Payment completion failed: {result['message']}")
        return False


def display_all_notifications():
    """Display all notifications created during the demo"""
    print("\n📬 All notifications created during payment flow test:")
    
    notifications = Notification.objects.filter(
        user__email__contains='payment_'
    ).order_by('-date')
    
    if not notifications.exists():
        print("   No notifications found")
        return
    
    for notification in notifications:
        print(f"   📧 {notification.user.email}: {notification.title}")
        print(f"      Type: {notification.type} | Priority: {notification.priority}")
        print(f"      Action URL: {notification.action_url}")
        print(f"      Message: {notification.message[:100]}...")
        print(f"      Metadata: {notification.metadata}")
        print()


def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up payment flow test data...")
    
    # Delete test notifications
    Notification.objects.filter(
        user__email__contains='payment_'
    ).delete()
    
    # Delete test payment intents
    PaymentIntent.objects.filter(
        buyer__email__contains='payment_'
    ).delete()
    
    # Delete test bids
    Bid.objects.filter(
        user__email__contains='payment_'
    ).delete()
    
    # Delete test auctions
    Ad.objects.filter(
        title__contains='Payment Flow Test'
    ).delete()
    
    # Delete test stripe accounts
    StripeAccount.objects.filter(
        user__email__contains='payment_'
    ).delete()
    
    # Delete test users
    User.objects.filter(
        email__contains='payment_'
    ).delete()
    
    print("   ✅ Payment flow test data cleaned up")


def main():
    """Main demo function"""
    print("🚀 Starting Payment Flow Integration Demo")
    print("=" * 60)
    
    try:
        # Create test data
        test_data = create_test_data()
        
        # Test auction closure with notifications
        auction_success = test_auction_closure_with_notifications(test_data)
        
        # Test payment intent creation
        payment_intent_success = test_payment_intent_creation(test_data)
        
        # Test payment completion
        payment_completion_success = test_payment_completion(test_data)
        
        # Display all notifications
        display_all_notifications()
        
        # Summary
        print("\n📊 Payment Flow Demo Summary:")
        print(f"   Auction closure: {'✅ PASSED' if auction_success else '❌ FAILED'}")
        print(f"   Payment intent creation: {'✅ PASSED' if payment_intent_success else '❌ FAILED'}")
        print(f"   Payment completion: {'✅ PASSED' if payment_completion_success else '❌ FAILED'}")
        
        if auction_success and payment_intent_success and payment_completion_success:
            print("\n🎉 All payment flow tests passed! The integration is working correctly.")
        else:
            print("\n⚠️  Some payment flow tests failed. Please check the implementation.")
        
    except Exception as e:
        print(f"\n❌ Payment flow demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        cleanup_test_data()
    
    print("\n✅ Payment flow demo completed!")


if __name__ == '__main__':
    main()
