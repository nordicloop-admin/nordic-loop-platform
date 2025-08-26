#!/usr/bin/env python3
"""
Test script for Winning Bids API endpoints

This script tests the improved winning bids API endpoints to ensure they work correctly
with the new 'paid' status and follow DRY/KISS principles.
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from rest_framework.test import force_authenticate
from ads.models import Ad
from bids.models import Bid
from bids.views import WinningBidsView, UserBidsListView
from categories.models import Category, Subcategory
from locations.models import Location

User = get_user_model()


def create_test_data():
    """Create test data for API testing"""
    print("🔧 Creating test data...")
    
    # Create test user
    user, _ = User.objects.get_or_create(
        username='api_test_user@test.com',
        defaults={
            'email': 'api_test_user@test.com',
            'first_name': 'API',
            'last_name': 'Test'
        }
    )
    
    # Create category and location
    category, _ = Category.objects.get_or_create(name='API Test Materials')
    subcategory, _ = Subcategory.objects.get_or_create(
        name='API Test Plastic',
        defaults={'category': category}
    )
    location, _ = Location.objects.get_or_create(
        country='API Test Country',
        defaults={'city': 'API Test City'}
    )
    
    # Create test auction
    auction = Ad.objects.create(
        user=user,
        category=category,
        subcategory=subcategory,
        location=location,
        title='API Test Auction',
        description='Test auction for API testing',
        available_quantity=Decimal('100.00'),
        unit_of_measurement='tons',
        starting_bid_price=Decimal('50.00'),
        currency='EUR',
        auction_duration=7,
        is_complete=True,
        is_active=True
    )
    
    # Create bids with different statuses
    bids = []
    
    # Won bid (needs payment)
    won_bid = Bid.objects.create(
        user=user,
        ad=auction,
        bid_price_per_unit=Decimal('85.00'),
        volume_requested=Decimal('50.00'),
        status='won'
    )
    bids.append(won_bid)
    
    # Paid bid (payment completed)
    paid_bid = Bid.objects.create(
        user=user,
        ad=auction,
        bid_price_per_unit=Decimal('90.00'),
        volume_requested=Decimal('30.00'),
        status='paid'
    )
    bids.append(paid_bid)
    
    # Winning bid (currently winning)
    winning_bid = Bid.objects.create(
        user=user,
        ad=auction,
        bid_price_per_unit=Decimal('95.00'),
        volume_requested=Decimal('20.00'),
        status='winning'
    )
    bids.append(winning_bid)
    
    print(f"✅ Created test data:")
    print(f"   - User: {user.email}")
    print(f"   - Auction: {auction.title}")
    print(f"   - Won bid: {won_bid.bid_price_per_unit} EUR/ton (status: {won_bid.status})")
    print(f"   - Paid bid: {paid_bid.bid_price_per_unit} EUR/ton (status: {paid_bid.status})")
    print(f"   - Winning bid: {winning_bid.bid_price_per_unit} EUR/ton (status: {winning_bid.status})")
    
    return user, auction, bids


def test_winning_bids_endpoint(user):
    """Test the /api/bids/winning/ endpoint"""
    print("\n🧪 Testing /api/bids/winning/ endpoint...")
    
    factory = RequestFactory()
    request = factory.get('/api/bids/winning/?page=1&page_size=10')
    force_authenticate(request, user=user)
    
    view = WinningBidsView()
    response = view.get(request)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.data
        print(f"   ✅ Success! Found {data['count']} winning bids")
        print(f"   Pagination: Page {data['current_page']} of {data['total_pages']}")
        
        for i, bid in enumerate(data['results']):
            print(f"   Bid {i+1}: {bid['bid_price_per_unit']} {bid['currency']}/unit (Status: {bid['status']})")
        
        return True
    else:
        print(f"   ❌ Failed: {response.data}")
        return False


def test_user_bids_with_status_filter(user):
    """Test the /api/bids/my/ endpoint with status filtering"""
    print("\n🧪 Testing /api/bids/my/ endpoint with status filters...")
    
    factory = RequestFactory()
    
    # Test different status filters
    statuses_to_test = ['won', 'paid', 'winning', 'all']
    
    for status in statuses_to_test:
        print(f"\n   Testing status filter: {status}")
        
        request = factory.get(f'/api/bids/my/?page=1&page_size=10&status={status}')
        force_authenticate(request, user=user)
        
        view = UserBidsListView()
        response = view.get(request)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.data
            print(f"   ✅ Found {data['count']} bids with status '{status}'")
            
            for bid in data['results']:
                print(f"     - {bid['bid_price_per_unit']} {bid['currency']}/unit (Status: {bid['status']})")
        else:
            print(f"   ❌ Failed: {response.data}")
            return False
    
    return True


def test_invalid_status_filter(user):
    """Test invalid status filter handling"""
    print("\n🧪 Testing invalid status filter handling...")
    
    factory = RequestFactory()
    request = factory.get('/api/bids/my/?status=invalid_status')
    force_authenticate(request, user=user)
    
    view = UserBidsListView()
    response = view.get(request)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print(f"   ✅ Correctly rejected invalid status: {response.data}")
        return True
    else:
        print(f"   ❌ Should have rejected invalid status but got: {response.data}")
        return False


def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete test bids
    Bid.objects.filter(user__email='api_test_user@test.com').delete()
    
    # Delete test auctions
    Ad.objects.filter(title='API Test Auction').delete()
    
    # Delete test user
    User.objects.filter(email='api_test_user@test.com').delete()
    
    print("   ✅ Test data cleaned up")


def main():
    """Main test function"""
    print("🚀 Starting Winning Bids API Tests")
    print("=" * 50)
    
    try:
        # Create test data
        user, auction, bids = create_test_data()
        
        # Test winning bids endpoint
        winning_bids_success = test_winning_bids_endpoint(user)
        
        # Test user bids with status filtering
        user_bids_success = test_user_bids_with_status_filter(user)
        
        # Test invalid status handling
        invalid_status_success = test_invalid_status_filter(user)
        
        # Summary
        print("\n📊 API Test Summary:")
        print(f"   Winning bids endpoint: {'✅ PASSED' if winning_bids_success else '❌ FAILED'}")
        print(f"   User bids with filtering: {'✅ PASSED' if user_bids_success else '❌ FAILED'}")
        print(f"   Invalid status handling: {'✅ PASSED' if invalid_status_success else '❌ FAILED'}")
        
        if winning_bids_success and user_bids_success and invalid_status_success:
            print("\n🎉 All API tests passed! The endpoints are working correctly.")
        else:
            print("\n⚠️  Some API tests failed. Please check the implementation.")
        
    except Exception as e:
        print(f"\n❌ API tests failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        cleanup_test_data()
    
    print("\n✅ API tests completed!")


if __name__ == '__main__':
    main()
