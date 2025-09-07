#!/usr/bin/env python
"""
Test script to verify the bidding system fix
This script tests that users cannot bid the same amount or lower than existing bids
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from bids.models import Bid
from ads.models import Ad
from company.models import Company
from bids.services import BidService
from bids.repository import BidRepository
from rest_framework.exceptions import ValidationError

User = get_user_model()


def create_test_users_and_ad():
    """Create test users, company, and ad for bidding test"""
    import time
    timestamp = str(int(time.time()))
    
    # Create companies with unique identifiers
    company1 = Company.objects.create(
        official_name=f"Test Company 1 {timestamp}",
        vat_number=f"TEST001{timestamp}",
        email=f"company1{timestamp}@test.com",
        country="Sweden",
        sector="manufacturing",
        status="approved"
    )
    
    company2 = Company.objects.create(
        official_name=f"Test Company 2 {timestamp}", 
        vat_number=f"TEST002{timestamp}",
        email=f"company2{timestamp}@test.com",
        country="Sweden",
        sector="manufacturing",
        status="approved"
    )
    
    # Create users with unique identifiers
    user1 = User.objects.create_user(
        username=f"bidder1{timestamp}",
        email=f"bidder1{timestamp}@test.com",
        first_name="John",
        last_name="Doe",
        company=company1,
        can_place_bids=True,
        bank_country="SE",
        bank_currency="SEK",
        payout_frequency="weekly",
        payout_method="bank_transfer"
    )
    
    user2 = User.objects.create_user(
        username=f"bidder2{timestamp}", 
        email=f"bidder2{timestamp}@test.com",
        first_name="Jane",
        last_name="Smith",
        company=company2,
        can_place_bids=True,
        bank_country="SE",
        bank_currency="SEK",
        payout_frequency="weekly",
        payout_method="bank_transfer"
    )
    
    # Create ad seller
    seller = User.objects.create_user(
        username=f"seller{timestamp}",
        email=f"seller{timestamp}@test.com",
        first_name="Seller",
        last_name="User",
        company=company1,
        can_place_ads=True,
        bank_country="SE",
        bank_currency="SEK",
        payout_frequency="weekly", 
        payout_method="bank_transfer"
    )
    
    # Create test ad (simplified without all validations)
    from category.models import Category
    
    # Create category if it doesn't exist
    category, _ = Category.objects.get_or_create(
        name="Test Plastic"
    )
    
    ad = Ad.objects.create(
        user=seller,
        title=f"Test Plastic Material {timestamp}",
        category=category,
        available_quantity=Decimal("100.00"),
        unit_of_measurement="kg",
        starting_bid_price=Decimal("10.00"),
        currency="SEK",
        is_active=True,
        is_complete=True,
        allow_broker_bids=True
    )
    
    return user1, user2, ad


def test_bidding_validation():
    """Test that bidding validation prevents equal/lower bids"""
    print("🧪 Testing bidding validation system...")
    
    # Clean up any existing test data
    Bid.objects.filter(user__username__startswith='bidder').delete()
    User.objects.filter(username__startswith='bidder').delete()
    User.objects.filter(username__startswith='seller').delete()
    Company.objects.filter(vat_number__startswith='TEST00').delete()
    
    # Create test data
    user1, user2, ad = create_test_users_and_ad()
    
    # Initialize service
    repository = BidRepository()
    service = BidService(repository)
    
    print(f"📦 Created test ad: {ad.title}")
    print(f"💰 Starting bid price: {ad.starting_bid_price} {ad.currency}")
    print(f"👥 Test users: {user1.username}, {user2.username}")
    print()
    
    try:
        # Test 1: User1 places first bid of 15.00
        print("Test 1: User1 places first bid of 15.00")
        bid1 = service.create_bid(
            ad_id=ad.id,
            bid_price_per_unit=15.00,
            volume_requested=10.00,
            user=user1,
            notes="First bid"
        )
        print(f"✅ SUCCESS: User1 bid placed at {bid1.bid_price_per_unit}")
        print()
        
        # Test 2: User2 tries to place same amount (15.00) - should FAIL
        print("Test 2: User2 tries to place same amount (15.00) - should FAIL")
        try:
            bid2_same = service.create_bid(
                ad_id=ad.id,
                bid_price_per_unit=15.00,
                volume_requested=5.00,
                user=user2,
                notes="Same amount bid"
            )
            print(f"❌ FAILED: User2 was able to bid same amount {bid2_same.bid_price_per_unit}")
            return False
        except ValueError as e:
            print(f"✅ SUCCESS: User2 same amount bid rejected: {str(e)}")
        print()
        
        # Test 3: User2 tries to place lower amount (12.00) - should FAIL  
        print("Test 3: User2 tries to place lower amount (12.00) - should FAIL")
        try:
            bid2_lower = service.create_bid(
                ad_id=ad.id,
                bid_price_per_unit=12.00,
                volume_requested=5.00,
                user=user2,
                notes="Lower amount bid"
            )
            print(f"❌ FAILED: User2 was able to bid lower amount {bid2_lower.bid_price_per_unit}")
            return False
        except ValueError as e:
            print(f"✅ SUCCESS: User2 lower amount bid rejected: {str(e)}")
        print()
        
        # Test 4: User2 tries to place slightly lower amount (14.99) - should FAIL
        print("Test 4: User2 tries to place slightly lower amount (14.99) - should FAIL")
        try:
            bid2_slightly_lower = service.create_bid(
                ad_id=ad.id,
                bid_price_per_unit=14.99,
                volume_requested=5.00,
                user=user2,
                notes="Slightly lower bid"
            )
            print(f"❌ FAILED: User2 was able to bid slightly lower amount {bid2_slightly_lower.bid_price_per_unit}")
            return False
        except ValueError as e:
            print(f"✅ SUCCESS: User2 slightly lower bid rejected: {str(e)}")
        print()
        
        # Test 5: User2 places higher bid (20.00) - should SUCCEED
        print("Test 5: User2 places higher bid (20.00) - should SUCCEED")
        bid2_higher = service.create_bid(
            ad_id=ad.id,
            bid_price_per_unit=20.00,
            volume_requested=5.00,
            user=user2,
            notes="Higher bid"
        )
        print(f"✅ SUCCESS: User2 higher bid placed at {bid2_higher.bid_price_per_unit}")
        print()
        
        # Test 6: User1 tries to update their bid to same as User2 (20.00) - should FAIL
        print("Test 6: User1 tries to update their bid to same as User2 (20.00) - should FAIL")
        try:
            updated_bid1_same = service.update_bid(
                bid_id=bid1.id,
                bid_price_per_unit=20.00,
                user=user1
            )
            print(f"❌ FAILED: User1 was able to update to same amount {updated_bid1_same.bid_price_per_unit}")
            return False
        except ValueError as e:
            print(f"✅ SUCCESS: User1 same amount update rejected: {str(e)}")
        print()
        
        # Test 7: User1 tries to update their bid to lower than User2 (18.00) - should FAIL
        print("Test 7: User1 tries to update their bid to lower than User2 (18.00) - should FAIL")
        try:
            updated_bid1_lower = service.update_bid(
                bid_id=bid1.id,
                bid_price_per_unit=18.00,
                user=user1
            )
            print(f"❌ FAILED: User1 was able to update to lower amount {updated_bid1_lower.bid_price_per_unit}")
            return False
        except ValueError as e:
            print(f"✅ SUCCESS: User1 lower amount update rejected: {str(e)}")
        print()
        
        # Test 8: User1 updates their bid to higher amount (25.00) - should SUCCEED
        print("Test 8: User1 updates their bid to higher amount (25.00) - should SUCCEED")
        updated_bid1_higher = service.update_bid(
            bid_id=bid1.id,
            bid_price_per_unit=25.00,
            user=user1
        )
        print(f"✅ SUCCESS: User1 higher update placed at {updated_bid1_higher.bid_price_per_unit}")
        print()
        
        # Test 9: Verify final bid statuses
        print("Test 9: Verify final bid statuses")
        final_bid1 = Bid.objects.get(id=bid1.id)
        final_bid2 = Bid.objects.get(id=bid2_higher.id)
        
        print(f"👑 User1 final bid: {final_bid1.bid_price_per_unit} (Status: {final_bid1.status})")
        print(f"📍 User2 final bid: {final_bid2.bid_price_per_unit} (Status: {final_bid2.status})")
        
        # Check that the higher bid is winning
        if final_bid1.bid_price_per_unit > final_bid2.bid_price_per_unit:
            if final_bid1.status != 'winning':
                print(f"❌ FAILED: User1 should be winning but status is {final_bid1.status}")
                return False
            print(f"✅ SUCCESS: User1 is winning with higher bid")
        else:
            print(f"❌ FAILED: Bid amounts not as expected")
            return False
            
        print()
        print("🎉 ALL TESTS PASSED! Bidding validation is working correctly.")
        print("✅ Users cannot bid equal or lower amounts than existing bids")
        print("✅ Users cannot update their bids to equal or lower amounts than other users' bids")
        print("✅ Users can only bid higher amounts than existing bids")
        
        return True
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_edge_cases():
    """Test edge cases for bidding validation"""
    print("\n🔍 Testing edge cases...")
    
    # Clean up
    Bid.objects.filter(user__username__startswith='bidder').delete()
    User.objects.filter(username__startswith='bidder').delete()
    User.objects.filter(username__startswith='seller').delete()
    Company.objects.filter(vat_number__startswith='TEST00').delete()
    
    # Create test data
    user1, user2, ad = create_test_users_and_ad()
    repository = BidRepository()
    service = BidService(repository)
    
    try:
        # Edge Case 1: User can still bid starting price if no other bids exist
        print("Edge Case 1: User can bid starting price when no other bids exist")
        bid1 = service.create_bid(
            ad_id=ad.id,
            bid_price_per_unit=float(ad.starting_bid_price),  # Exact starting price
            volume_requested=10.00,
            user=user1
        )
        print(f"✅ SUCCESS: User1 can bid starting price {bid1.bid_price_per_unit}")
        
        # Edge Case 2: User can update their own bid higher when they're the only bidder
        print("Edge Case 2: User can update their own bid when they're the only bidder")
        updated_bid = service.update_bid(
            bid_id=bid1.id,
            bid_price_per_unit=12.00,
            user=user1
        )
        print(f"✅ SUCCESS: User1 can update their bid to {updated_bid.bid_price_per_unit}")
        
        print("\n🎉 Edge cases passed!")
        return True
        
    except Exception as e:
        print(f"❌ Edge case error: {str(e)}")
        return False


if __name__ == "__main__":
    print("🚀 Starting bidding validation tests...\n")
    
    success1 = test_bidding_validation()
    success2 = test_edge_cases()
    
    if success1 and success2:
        print("\n🎊 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("The bidding bug has been fixed:")
        print("- Users cannot bid the same amount as existing bids")
        print("- Users cannot bid lower than existing bids") 
        print("- Users can only place bids higher than existing bids")
        print("- Update functionality also enforces these rules")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED!")
        print("The bidding bug fix needs more work.")
        sys.exit(1)
