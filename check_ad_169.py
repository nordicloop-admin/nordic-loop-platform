#!/usr/bin/env python3
"""
Check the current state of ad 169
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

def check_ad_169():
    """Check the current state of ad 169"""
    try:
        # Get the ad
        ad = Ad.objects.get(id=169)
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
        
        # Check specific fields
        print(f"\nField values:")
        print(f"  packaging: {ad.packaging}")
        print(f"  material_frequency: {ad.material_frequency}")
        print(f"  origin: {ad.origin}")
        print(f"  contamination: {ad.contamination}")
        print(f"  additives: {ad.additives}")
        print(f"  storage_conditions: {ad.storage_conditions}")
        print(f"  processing_methods: {ad.processing_methods}")
        print(f"  location: {ad.location}")
        print(f"  delivery_options: {ad.delivery_options}")
        print(f"  available_quantity: {ad.available_quantity}")
        print(f"  starting_bid_price: {ad.starting_bid_price}")
        print(f"  currency: {ad.currency}")
        print(f"  description: {ad.description}")
        
    except Ad.DoesNotExist:
        print("Ad with ID 169 not found")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_ad_169()
