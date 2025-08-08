#!/usr/bin/env python3
"""
Test script to check ad completion logic
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
from ads.serializer import AdUpdateSerializer

def test_ad_completion():
    """Test the ad completion logic for ad ID 169"""
    try:
        # Get the ad
        ad = Ad.objects.get(id=169)
        print(f"Ad ID: {ad.id}")
        print(f"Title: {ad.title}")
        print(f"Category: {ad.category.name if ad.category else 'None'}")
        print(f"Current is_complete: {ad.is_complete}")
        
        # Check step completion status
        step_status = ad.get_step_completion_status()
        print(f"Step completion status: {step_status}")
        
        # Check next incomplete step
        next_step = ad.get_next_incomplete_step()
        print(f"Next incomplete step: {next_step}")
        
        # Test the serializer's _is_complete method
        serializer = AdUpdateSerializer()
        is_complete_new = serializer._is_complete(ad)
        print(f"New _is_complete result: {is_complete_new}")
        
        # Update the ad to trigger the new completion logic
        print("\nUpdating ad to trigger completion recalculation...")
        serializer = AdUpdateSerializer(ad, data={}, partial=True)
        if serializer.is_valid():
            updated_ad = serializer.save()
            print(f"Updated is_complete: {updated_ad.is_complete}")
        else:
            print(f"Serializer errors: {serializer.errors}")
            
    except Ad.DoesNotExist:
        print("Ad with ID 169 not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ad_completion()
