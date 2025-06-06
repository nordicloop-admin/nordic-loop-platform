#!/usr/bin/env python
"""
Sample Bid Data Creation Script for Nordic Loop Platform

This script creates sample bid data to demonstrate the enhanced bidding system.
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from ads.models import Ad
from bids.models import Bid, BidHistory
from bids.services import BidService
from bids.repository import BidRepository

User = get_user_model()


def create_sample_bids():
    """Create sample bids for testing the enhanced bidding system"""
    
    print("Creating sample bid data...")
    
    # Get users for bidding
    try:
        seller = User.objects.get(username='john_seller')
        buyer1 = User.objects.get(username='jane_buyer')
        buyer2 = User.objects.get(username='mike_buyer')
        
        print("✓ Found existing users")
    except User.DoesNotExist:
        print("❌ Required users not found. Please run setup_test_data.py first")
        return
    
    # Get active ads for bidding
    active_ads = Ad.objects.filter(is_active=True, is_complete=True)[:3]
    
    if not active_ads:
        print("❌ No active ads found. Please run setup_test_data.py first")
        return
    
    print(f"✓ Found {len(active_ads)} active ads")
    
    # Clear existing bids
    Bid.objects.all().delete()
    BidHistory.objects.all().delete()
    print("✓ Cleared existing bid data")
    
    # Initialize bid service
    bid_repository = BidRepository()
    bid_service = BidService(bid_repository)
    
    # Create bids for each ad
    bid_count = 0
    
    for i, ad in enumerate(active_ads):
        print(f"\n📈 Creating bids for Ad #{ad.id}: {ad.title}")
        
        # Starting bid from buyer1
        starting_price = ad.starting_bid_price if ad.starting_bid_price else Decimal('50.00')
        bid1_price = starting_price + Decimal('5.00')
        
        try:
            bid1 = bid_service.create_bid(
                ad_id=ad.id,
                bid_price_per_unit=float(bid1_price),
                volume_requested=float(min(ad.available_quantity / 4, Decimal('25.00'))),
                user=buyer1,
                volume_type='partial',
                notes=f'Initial bid for {ad.title}',
                max_auto_bid_price=float(bid1_price + Decimal('10.00'))  # Enable auto-bidding
            )
            print(f"  ✓ Created bid from {buyer1.username}: {bid1_price} {ad.currency}")
            bid_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to create bid from {buyer1.username}: {e}")
            continue
        
        # Counter bid from buyer2
        bid2_price = bid1_price + Decimal('3.00')
        
        try:
            bid2 = bid_service.create_bid(
                ad_id=ad.id,
                bid_price_per_unit=float(bid2_price),
                volume_requested=float(min(ad.available_quantity / 3, Decimal('30.00'))),
                user=buyer2,
                volume_type='partial',
                notes=f'Counter bid for {ad.title}',
                max_auto_bid_price=float(bid2_price + Decimal('15.00'))  # Higher auto-bid limit
            )
            print(f"  ✓ Created bid from {buyer2.username}: {bid2_price} {ad.currency}")
            bid_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to create bid from {buyer2.username}: {e}")
        
        # Update buyer1's bid to demonstrate bid updates
        try:
            updated_price = bid2_price + Decimal('2.00')
            result = bid_service.update_bid(
                bid_id=bid1.id,
                bid_price_per_unit=float(updated_price),
                volume_requested=float(min(ad.available_quantity / 2, Decimal('40.00'))),
                user=buyer1,
                notes=f'Updated bid for {ad.title} - increased volume'
            )
            
            if 'error' not in result:
                print(f"  ✓ Updated bid from {buyer1.username}: {updated_price} {ad.currency}")
            else:
                print(f"  ❌ Failed to update bid: {result['error']}")
                
        except Exception as e:
            print(f"  ❌ Failed to update bid: {e}")
        
        # Final bid from buyer2 with full volume
        if i == 0:  # Only for first ad
            try:
                final_price = updated_price + Decimal('5.00')
                bid3 = bid_service.create_bid(
                    ad_id=ad.id,
                    bid_price_per_unit=float(final_price),
                    volume_requested=float(ad.available_quantity),  # Full volume
                    user=buyer2,
                    volume_type='full',
                    notes=f'Final bid for full volume of {ad.title}'
                )
                print(f"  ✓ Created final bid from {buyer2.username}: {final_price} {ad.currency} (full volume)")
                bid_count += 1
                
            except Exception as e:
                print(f"  ❌ Failed to create final bid: {e}")
    
    # Display statistics
    print(f"\n📊 Bid Creation Summary:")
    print(f"Total bids created: {bid_count}")
    
    # Show bid statistics for each ad
    for ad in active_ads:
        stats = bid_service.get_bid_statistics(ad.id)
        highest_bid = bid_service.get_highest_bid_for_ad(ad.id)
        
        print(f"\n🎯 Ad #{ad.id}: {ad.title}")
        print(f"  Total bids: {stats.get('total_bids', 0)}")
        print(f"  Unique bidders: {stats.get('unique_bidders', 0)}")
        
        if highest_bid:
            print(f"  Winning bid: {highest_bid.bid_price_per_unit} {ad.currency} by {highest_bid.user.username}")
            print(f"  Volume requested: {highest_bid.volume_requested} {ad.unit_of_measurement}")
            print(f"  Total value: {highest_bid.total_bid_value} {ad.currency}")
        else:
            print(f"  No bids found")
    
    # Show bid history
    print(f"\n📝 Recent Bid History:")
    recent_history = BidHistory.objects.all().order_by('-timestamp')[:10]
    
    for history in recent_history:
        print(f"  {history.timestamp.strftime('%Y-%m-%d %H:%M')} - {history.change_reason}: "
              f"{history.previous_price or 'N/A'} → {history.new_price} "
              f"(Bid #{history.bid.id})")
    
    print(f"\n✅ Sample bid data creation completed!")
    print(f"\n🔗 Test the bidding API endpoints:")
    print(f"   GET /api/bids/ad/{{ad_id}}/          - List bids for an ad")
    print(f"   GET /api/bids/ad/{{ad_id}}/stats/    - Get bid statistics")
    print(f"   GET /api/bids/user/                  - Get user's bids")
    print(f"   GET /api/bids/search/                - Search bids")
    print(f"   POST /api/bids/create/               - Create new bid")
    print(f"   PUT /api/bids/{{bid_id}}/update/     - Update existing bid")
    print(f"   DELETE /api/bids/{{bid_id}}/delete/  - Cancel bid")


if __name__ == '__main__':
    create_sample_bids() 