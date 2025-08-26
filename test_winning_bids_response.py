#!/usr/bin/env python3
"""
Test script to verify the winning bids API response structure

This script tests the enhanced winning bids API response to ensure it includes
all the fields expected by the frontend components.
"""

import os
import sys
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import force_authenticate
from bids.views import WinningBidsView
from bids.serializer import WinningBidSerializer
from bids.models import Bid

User = get_user_model()


def test_winning_bid_serializer():
    """Test the WinningBidSerializer directly"""
    print("🧪 Testing WinningBidSerializer...")
    
    # Get a sample winning bid
    winning_bid = Bid.objects.filter(status__in=['won', 'winning']).select_related('ad', 'user').first()
    
    if not winning_bid:
        print("   ❌ No winning bids found in database")
        return False
    
    # Serialize the bid
    serializer = WinningBidSerializer(winning_bid)
    data = serializer.data
    
    print(f"   ✅ Serialized winning bid data:")
    print(json.dumps(data, indent=2, default=str))
    
    # Check for expected fields
    expected_fields = [
        'id', 'ad_id', 'ad_title', 'bidder_name', 'company_name',
        'bid_price_per_unit', 'volume_requested', 'total_bid_value',
        'status', 'created_at', 'updated_at',
        'ad_category', 'ad_user_email', 'ad_location', 'currency', 'unit'
    ]
    
    missing_fields = []
    for field in expected_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"   ⚠️  Missing fields: {missing_fields}")
    else:
        print(f"   ✅ All expected fields present")
    
    return len(missing_fields) == 0


def test_winning_bids_api_response():
    """Test the full API response structure"""
    print("\n🧪 Testing WinningBidsView API response...")
    
    # Get a user with winning bids
    user = User.objects.filter(
        bids__status__in=['won', 'winning', 'paid']
    ).first()
    
    if not user:
        print("   ❌ No users with winning bids found")
        return False
    
    # Create request
    factory = RequestFactory()
    request = factory.get('/api/bids/winning/?page=1&page_size=5')
    force_authenticate(request, user=user)
    
    # Call the view
    view = WinningBidsView()
    response = view.get(request)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   ❌ API call failed: {response.data}")
        return False
    
    data = response.data
    
    # Check response structure
    expected_keys = ['count', 'next', 'previous', 'page_size', 'total_pages', 'current_page', 'results']
    missing_keys = [key for key in expected_keys if key not in data]
    
    if missing_keys:
        print(f"   ❌ Missing response keys: {missing_keys}")
        return False
    
    print(f"   ✅ Response structure correct")
    print(f"   Found {data['count']} winning bids")
    
    # Check first result structure if available
    if data['results']:
        first_bid = data['results'][0]
        print(f"\n   📋 First bid structure:")
        print(json.dumps(first_bid, indent=4, default=str))
        
        # Check for frontend-expected fields
        frontend_fields = [
            'id', 'ad_title', 'bid_price_per_unit', 'volume_requested', 
            'total_bid_value', 'status', 'currency', 'unit',
            'ad_category', 'ad_user_email', 'ad_location'
        ]
        
        missing_frontend_fields = [field for field in frontend_fields if field not in first_bid]
        
        if missing_frontend_fields:
            print(f"   ⚠️  Missing frontend fields: {missing_frontend_fields}")
        else:
            print(f"   ✅ All frontend-expected fields present")
        
        return len(missing_frontend_fields) == 0
    else:
        print(f"   ℹ️  No results to check field structure")
        return True


def main():
    """Main test function"""
    print("🚀 Testing Winning Bids API Response Structure")
    print("=" * 60)
    
    try:
        # Test serializer directly
        serializer_success = test_winning_bid_serializer()
        
        # Test full API response
        api_success = test_winning_bids_api_response()
        
        # Summary
        print("\n📊 Test Summary:")
        print(f"   Serializer test: {'✅ PASSED' if serializer_success else '❌ FAILED'}")
        print(f"   API response test: {'✅ PASSED' if api_success else '❌ FAILED'}")
        
        if serializer_success and api_success:
            print("\n🎉 All tests passed! The API response structure is correct.")
        else:
            print("\n⚠️  Some tests failed. Please check the implementation.")
        
    except Exception as e:
        print(f"\n❌ Tests failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Response structure tests completed!")


if __name__ == '__main__':
    main()
