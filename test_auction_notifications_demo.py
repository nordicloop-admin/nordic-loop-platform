#!/usr/bin/env python3
"""
Demo script to test the auction notification system

This script demonstrates the automated auction notification system by:
1. Creating sample auctions and bids
2. Testing automatic auction closure
3. Testing manual admin closure
4. Verifying notifications are sent correctly

Run this script to validate the implementation works as expected.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nordic_loop_platform.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from ads.models import Ad
from ads.auction_services.auction_completion import AuctionCompletionService
from bids.models import Bid
from bids.services import BidService
from notifications.models import Notification
from categories.models import Category, Subcategory
from locations.models import Location

User = get_user_model()


def create_test_data():
    """Create test users, auction, and bids"""
    print("🔧 Creating test data...")
    
    # Create test users
    seller, _ = User.objects.get_or_create(
        username='demo_seller@test.com',
        defaults={
            'email': 'demo_seller@test.com',
            'first_name': 'Demo',
            'last_name': 'Seller'
        }
    )
    
    bidder1, _ = User.objects.get_or_create(
        username='demo_bidder1@test.com',
        defaults={
            'email': 'demo_bidder1@test.com',
            'first_name': 'Demo',
            'last_name': 'Bidder1'
        }
    )
    
    bidder2, _ = User.objects.get_or_create(
        username='demo_bidder2@test.com',
        defaults={
            'email': 'demo_bidder2@test.com',
            'first_name': 'Demo',
            'last_name': 'Bidder2'
        }
    )
    
    # Create category and location
    category, _ = Category.objects.get_or_create(name='Demo Materials')
    subcategory, _ = Subcategory.objects.get_or_create(
        name='Demo Plastic',
        defaults={'category': category}
    )
    location, _ = Location.objects.get_or_create(
        country='Demo Country',
        defaults={'city': 'Demo City'}
    )
    
    # Create expired auction for automatic closure test
    expired_auction = Ad.objects.create(
        user=seller,
        category=category,
        subcategory=subcategory,
        location=location,
        title='Demo Expired Auction',
        description='This auction has expired and should be closed automatically',
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
    
    # Create active auction for manual closure test
    active_auction = Ad.objects.create(
        user=seller,
        category=category,
        subcategory=subcategory,
        location=location,
        title='Demo Active Auction',
        description='This auction is active and will be closed manually',
        available_quantity=Decimal('200.00'),
        unit_of_measurement='tons',
        starting_bid_price=Decimal('40.00'),
        currency='EUR',
        auction_duration=14,
        is_complete=True,
        is_active=True,
        auction_start_date=timezone.now() - timedelta(days=1),
        auction_end_date=timezone.now() + timedelta(days=13)  # Still active
    )
    
    # Create bids for expired auction
    winning_bid_expired = Bid.objects.create(
        user=bidder1,
        ad=expired_auction,
        bid_price_per_unit=Decimal('75.00'),
        volume_requested=Decimal('50.00'),
        status='active'
    )
    
    losing_bid_expired = Bid.objects.create(
        user=bidder2,
        ad=expired_auction,
        bid_price_per_unit=Decimal('65.00'),
        volume_requested=Decimal('30.00'),
        status='active'
    )
    
    # Create bids for active auction
    winning_bid_active = Bid.objects.create(
        user=bidder2,
        ad=active_auction,
        bid_price_per_unit=Decimal('85.00'),
        volume_requested=Decimal('75.00'),
        status='active'
    )
    
    losing_bid_active = Bid.objects.create(
        user=bidder1,
        ad=active_auction,
        bid_price_per_unit=Decimal('70.00'),
        volume_requested=Decimal('40.00'),
        status='active'
    )
    
    print(f"✅ Created test data:")
    print(f"   - Users: {seller.email}, {bidder1.email}, {bidder2.email}")
    print(f"   - Expired auction: {expired_auction.title} (ID: {expired_auction.id})")
    print(f"   - Active auction: {active_auction.title} (ID: {active_auction.id})")
    print(f"   - Total bids created: 4")
    
    return {
        'seller': seller,
        'bidder1': bidder1,
        'bidder2': bidder2,
        'expired_auction': expired_auction,
        'active_auction': active_auction,
        'winning_bid_expired': winning_bid_expired,
        'winning_bid_active': winning_bid_active
    }


def test_automatic_closure(test_data):
    """Test automatic auction closure"""
    print("\n🤖 Testing automatic auction closure...")
    
    auction_service = AuctionCompletionService()
    
    # Find expired auctions
    expired_auctions = auction_service.get_expired_auctions(grace_period_minutes=5)
    print(f"   Found {len(expired_auctions)} expired auctions")
    
    if not expired_auctions:
        print("   ❌ No expired auctions found")
        return False
    
    # Close the expired auction
    result = auction_service.close_auction_with_notifications(test_data['expired_auction'])
    
    print(f"   Closure result: {result}")
    
    if result['success'] and result['has_winner']:
        print(f"   ✅ Auction closed successfully")
        print(f"   Winner: {result['winner_email']}")
        print(f"   Winning price: {result['winning_price']} {result['currency']}")
        
        # Check notification was sent
        notifications = Notification.objects.filter(
            user=test_data['bidder1'],
            type='auction',
            metadata__action_type='auction_won'
        )
        
        if notifications.exists():
            notification = notifications.first()
            print(f"   ✅ Winner notification sent: '{notification.title}'")
            return True
        else:
            print(f"   ❌ Winner notification not found")
            return False
    else:
        print(f"   ❌ Auction closure failed: {result.get('message', 'Unknown error')}")
        return False


def test_manual_closure(test_data):
    """Test manual admin closure"""
    print("\n👨‍💼 Testing manual admin closure...")
    
    bid_service = BidService()
    
    # Manually mark bid as won (simulating admin action)
    result = bid_service.admin_mark_bid_as_won(
        test_data['winning_bid_active'].id,
        test_data['seller']  # Using seller as admin for demo
    )
    
    print(f"   Manual closure result: {result}")
    
    if result['success']:
        print(f"   ✅ Bid marked as won successfully")
        
        # Check notification was sent
        notifications = Notification.objects.filter(
            user=test_data['bidder2'],
            type='auction',
            metadata__action_type='auction_won'
        )
        
        if notifications.exists():
            notification = notifications.first()
            print(f"   ✅ Winner notification sent: '{notification.title}'")
            print(f"   Notification type: {notification.metadata.get('closure_type', 'unknown')}")
            return True
        else:
            print(f"   ❌ Winner notification not found")
            return False
    else:
        print(f"   ❌ Manual closure failed: {result.get('message', 'Unknown error')}")
        return False


def display_all_notifications():
    """Display all notifications created during the demo"""
    print("\n📬 All notifications created:")
    
    notifications = Notification.objects.filter(
        type__in=['auction', 'bid']
    ).order_by('-date')
    
    if not notifications.exists():
        print("   No notifications found")
        return
    
    for notification in notifications:
        print(f"   📧 {notification.user.email}: {notification.title}")
        print(f"      Type: {notification.type} | Priority: {notification.priority}")
        print(f"      Message: {notification.message[:100]}...")
        print(f"      Metadata: {notification.metadata}")
        print()


def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete test notifications
    Notification.objects.filter(
        user__email__contains='demo_'
    ).delete()
    
    # Delete test bids
    Bid.objects.filter(
        user__email__contains='demo_'
    ).delete()
    
    # Delete test auctions
    Ad.objects.filter(
        title__contains='Demo'
    ).delete()
    
    # Delete test users
    User.objects.filter(
        email__contains='demo_'
    ).delete()
    
    print("   ✅ Test data cleaned up")


def main():
    """Main demo function"""
    print("🚀 Starting Auction Notification System Demo")
    print("=" * 50)
    
    try:
        # Create test data
        test_data = create_test_data()
        
        # Test automatic closure
        auto_success = test_automatic_closure(test_data)
        
        # Test manual closure
        manual_success = test_manual_closure(test_data)
        
        # Display all notifications
        display_all_notifications()
        
        # Summary
        print("\n📊 Demo Summary:")
        print(f"   Automatic closure: {'✅ PASSED' if auto_success else '❌ FAILED'}")
        print(f"   Manual closure: {'✅ PASSED' if manual_success else '❌ FAILED'}")
        
        if auto_success and manual_success:
            print("\n🎉 All tests passed! The auction notification system is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Please check the implementation.")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        cleanup_test_data()
    
    print("\n✅ Demo completed!")


if __name__ == '__main__':
    main()
