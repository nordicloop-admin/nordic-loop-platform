#!/usr/bin/env python3
"""
Check the current state of ad 209
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

def check_ad_209():
    """Check the current state of ad 209"""
    try:
        # Get the ad
        ad = Ad.objects.get(id=209)
        print(f"Ad ID: {ad.id}")
        print(f"Title: {ad.title}")
        print(f"Category: {ad.category.name if ad.category else 'None'}")
        print(f"Subcategory: {ad.subcategory.name if ad.subcategory else 'None'}")
        print(f"is_active: {ad.is_active}")
        print(f"is_complete: {ad.is_complete}")
        print(f"current_step: {ad.current_step}")
        
        # Check step completion status
        step_status = ad.get_step_completion_status()
        print(f"Step completion status: {step_status}")
        
        # Check next incomplete step
        next_step = ad.get_next_incomplete_step()
        print(f"Next incomplete step: {next_step}")
        
        # Test the serializer's _is_complete method
        serializer = AdUpdateSerializer()
        is_complete_new = serializer._is_complete(ad)
        print(f"Serializer _is_complete result: {is_complete_new}")
        
        # Check specific fields that might be missing
        print(f"\nField values:")
        print(f"  category: {ad.category}")
        print(f"  subcategory: {ad.subcategory}")
        print(f"  packaging: {ad.packaging}")
        print(f"  material_frequency: {ad.material_frequency}")
        print(f"  location: {ad.location}")
        print(f"  delivery_options: {ad.delivery_options}")
        print(f"  available_quantity: {ad.available_quantity}")
        print(f"  starting_bid_price: {ad.starting_bid_price}")
        print(f"  currency: {ad.currency}")
        print(f"  title: {ad.title}")
        print(f"  description: {ad.description}")
        
        # For plastic materials, check additional fields
        if ad.category and ad.category.name.lower() in ['plastic', 'plastics']:
            print(f"\nPlastic-specific fields:")
            print(f"  specification: {ad.specification}")
            print(f"  additional_specifications: {ad.additional_specifications}")
            print(f"  origin: {ad.origin}")
            print(f"  contamination: {ad.contamination}")
            print(f"  additives: {ad.additives}")
            print(f"  storage_conditions: {ad.storage_conditions}")
            print(f"  processing_methods: {ad.processing_methods}")
        
    except Ad.DoesNotExist:
        print("Ad with ID 209 not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ad_209()
