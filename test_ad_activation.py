#!/usr/bin/env python3
"""
Test script to check ad activation
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from ads.models import Ad
from ads.services import AdService
from ads.repository import AdRepository
from users.models import User

def test_ad_activation():
    """Test the ad activation for ad ID 169"""
    try:
        # Get the ad
        ad = Ad.objects.get(id=169)
        print(f"Ad ID: {ad.id}")
        print(f"Title: {ad.title}")
        print(f"Category: {ad.category.name if ad.category else 'None'}")
        print(f"is_complete: {ad.is_complete}")
        print(f"is_active: {ad.is_active}")
        print(f"status: {ad.status}")
        print(f"suspended_by_admin: {ad.suspended_by_admin}")
        
        # Get the user who owns this ad
        user = ad.user
        print(f"Owner: {user.username}")
        
        # Test activation using the service
        print("\nTesting activation...")
        ad_service = AdService(AdRepository())
        
        try:
            activated_ad = ad_service.activate_ad(ad.id, user)
            print(f"Activation successful!")
            print(f"New is_active: {activated_ad.is_active}")
            print(f"Auction start date: {activated_ad.auction_start_date}")
            print(f"Auction end date: {activated_ad.auction_end_date}")
        except Exception as e:
            print(f"Activation failed: {e}")
            
    except Ad.DoesNotExist:
        print("Ad with ID 169 not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ad_activation()
