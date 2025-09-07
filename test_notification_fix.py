#!/usr/bin/env python3
"""
Test script to verify that the notification fix prevents duplicate auction winner notifications
and ensures only one notification with the correct automatic payment message is sent.
"""

import os
import django
import sys
from datetime import timedelta
from decimal import Decimal

# Setup Django environment
sys.path.append('/home/okarera/Documents/Personal/Projects/Side Projects/Noordic Loop Market Place/nordic-loop-platform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from ads.models import Ad, Category, SubCategory, Location
from bids.models import Bid
from notifications.models import Notification
from bids.services import BidService
from bids.repository import BidRepository
from ads.auction_services.auction_completion import AuctionCompletionService

User = get_user_model()

def cleanup_test_data():
    """Clean up any existing test data"""
    print("🧹 Cleaning up existing test data...")
    
    # Delete test notifications
    Notification.objects.filter(
        title__icontains='Test Auction'
    ).delete()
    
    # Delete test bids
    Bid.objects.filter(
        ad__title__icontains='Test Auction'
    ).delete()
    
    # Delete test ads
    Ad.objects.filter(
        title__icontains='Test Auction'
    ).delete()
    
    # Delete test users
    User.objects.filter(
        email__contains='notificationtest'
    ).delete()
    
    print("✅ Cleanup completed")

def create_test_data():
    """Create test data for notification testing"""
    print("📦 Creating test data...")
    
    # Create test users
    seller = User.objects.create_user(
        username='seller_notificationtest',
        email='seller_notificationtest@test.com',
        password='testpass123',
        first_name='Seller',
        last_name='User'
    )
    
    buyer = User.objects.create_user(
        username='buyer_notificationtest',
        email='buyer_notificationtest@test.com',
        password='testpass123',
        first_name='Buyer',
        last_name='User'
    )
    
    # Get or create category and subcategory
    category, _ = Category.objects.get_or_create(name='Electronics')
    subcategory, _ = SubCategory.objects.get_or_create(name='PCB', category=category)
    location = Location.objects.first()  # Use existing location
    
    # Create test auction
    auction_end = timezone.now() + timedelta(minutes=1)  # End in 1 minute
    
    ad = Ad.objects.create(
        user=seller,
        title='Test Auction - Notification Fix',
        description='Test auction for verifying notification fixes',
        category=category,
        subcategory=subcategory,
        location=location,
        available_quantity=100.00,
        unit_of_measurement='kg',
        starting_bid_price=10.00,
        currency='EUR',
        auction_start_date=timezone.now(),
        auction_end_date=auction_end,
        is_active=True,
        is_complete=True,
        status='active'
    )
    
    print(f"✅ Created test auction: {ad.title} (ID: {ad.id})")
    print(f"   Seller: {seller.email}")
    print(f"   Buyer: {buyer.email}")
    
    return seller, buyer, ad

def test_single_notification():
    """Test that only one notification is sent for auction winner"""
    print("\n🧪 Testing single notification for auction winner...")
    
    seller, buyer, ad = create_test_data()
    bid_service = BidService(BidRepository())
    auction_service = AuctionCompletionService()
    
    try:
        # Place a winning bid
        print("📝 Placing winning bid...")
        winning_bid = bid_service.create_bid(
            ad_id=ad.id,
            bid_price_per_unit=25.00,
            volume_requested=50.00,
            user=buyer,
            notes="Test winning bid"
        )
        print(f"✅ Bid placed: {winning_bid.bid_price_per_unit} EUR per kg for {winning_bid.volume_requested} kg")
        
        # Check notifications before closing auction
        notifications_before = Notification.objects.filter(user=buyer).count()
        print(f"📊 Notifications before auction closure: {notifications_before}")
        
        # Close the auction manually (simulating admin action)
        print("🔚 Closing auction manually...")
        result = auction_service.close_auction_manually(ad, winning_bid)
        
        if result['success']:
            print(f"✅ Auction closed successfully")
            print(f"   Winner: {result['winner_email']}")
            print(f"   Winning price: {result['winning_price']} EUR per kg")
            print(f"   Notification sent: {result['notification_sent']}")
        else:
            print(f"❌ Failed to close auction: {result['message']}")
            return False
        
        # Check notifications after closing auction
        notifications_after = Notification.objects.filter(user=buyer)
        notification_count = notifications_after.count()
        print(f"📊 Notifications after auction closure: {notification_count}")
        
        # Verify only one notification was sent
        if notification_count == notifications_before + 1:
            notification = notifications_after.latest('date')
            print(f"✅ SUCCESS: Only one notification sent")
            print(f"   Title: {notification.title}")
            print(f"   Message: {notification.message[:100]}...")
            
            # Check if message mentions automatic payment processing
            if "automatically processed" in notification.message:
                print("✅ SUCCESS: Notification correctly mentions automatic payment processing")
                return True
            else:
                print("❌ FAIL: Notification does not mention automatic payment processing")
                return False
        else:
            print(f"❌ FAIL: Expected 1 new notification, got {notification_count - notifications_before}")
            if notification_count > notifications_before + 1:
                print("   Multiple notifications detected:")
                for i, notif in enumerate(notifications_after.order_by('-date')[:3], 1):
                    print(f"   {i}. {notif.title}: {notif.message[:80]}...")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_duplicate_prevention():
    """Test that duplicate notifications are prevented"""
    print("\n🧪 Testing duplicate notification prevention...")
    
    seller, buyer, ad = create_test_data()
    bid_service = BidService(BidRepository())
    auction_service = AuctionCompletionService()
    
    try:
        # Place a winning bid
        winning_bid = bid_service.create_bid(
            ad_id=ad.id,
            bid_price_per_unit=30.00,
            volume_requested=40.00,
            user=buyer,
            notes="Test duplicate prevention bid"
        )
        
        notifications_before = Notification.objects.filter(user=buyer).count()
        
        # Close auction twice (should only create one notification)
        print("🔚 Closing auction first time...")
        result1 = auction_service.close_auction_manually(ad, winning_bid)
        
        # Reset ad to active status to test duplicate
        ad.is_active = True
        ad.status = 'active'
        ad.save()
        
        print("🔚 Attempting to close auction second time...")
        result2 = auction_service.close_auction_manually(ad, winning_bid)
        
        notifications_after = Notification.objects.filter(user=buyer).count()
        notification_diff = notifications_after - notifications_before
        
        print(f"📊 Notifications created: {notification_diff}")
        
        if notification_diff == 1:
            print("✅ SUCCESS: Duplicate notification prevented")
            return True
        else:
            print(f"❌ FAIL: Expected 1 notification, got {notification_diff}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_message_content():
    """Test that the notification message content is correct"""
    print("\n🧪 Testing notification message content...")
    
    seller, buyer, ad = create_test_data()
    bid_service = BidService(BidRepository())
    auction_service = AuctionCompletionService()
    
    try:
        # Place a winning bid
        winning_bid = bid_service.create_bid(
            ad_id=ad.id,
            bid_price_per_unit=35.00,
            volume_requested=60.00,
            user=buyer,
            notes="Test message content bid"
        )
        
        # Close auction
        result = auction_service.close_auction_manually(ad, winning_bid)
        
        if result['success']:
            # Get the notification
            notification = Notification.objects.filter(user=buyer).latest('date')
            
            expected_phrases = [
                "Great news!",
                "won the auction",
                ad.title,
                "35.00 EUR per kg",
                "60.00 kg",
                "automatically processed",
                "purchase is complete"
            ]
            
            success = True
            for phrase in expected_phrases:
                if phrase not in notification.message:
                    print(f"❌ FAIL: Missing phrase '{phrase}' in notification")
                    success = False
                else:
                    print(f"✅ Found phrase: '{phrase}'")
            
            if success:
                print("✅ SUCCESS: All expected phrases found in notification message")
                print(f"📝 Full message: {notification.message}")
                return True
            else:
                print(f"❌ FAIL: Some expected phrases missing")
                print(f"📝 Actual message: {notification.message}")
                return False
        else:
            print(f"❌ Failed to close auction: {result['message']}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all notification fix tests"""
    print("🚀 Starting notification fix tests...")
    print("=" * 60)
    
    # Cleanup before starting
    cleanup_test_data()
    
    # Run tests
    test_results = []
    
    test_results.append(("Single Notification Test", test_single_notification()))
    cleanup_test_data()
    
    test_results.append(("Duplicate Prevention Test", test_duplicate_prevention()))
    cleanup_test_data()
    
    test_results.append(("Message Content Test", test_message_content()))
    cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The notification fix is working correctly.")
        print("✅ Users will now receive only one notification with the correct automatic payment message.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    # Final cleanup
    cleanup_test_data()

if __name__ == '__main__':
    main()
