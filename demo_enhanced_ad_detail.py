#!/usr/bin/env python3
"""
Demo script to showcase the enhanced ad detail functionality.
This script demonstrates all the comprehensive information returned by the ad detail endpoint.
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from ads.models import Ad
from ads.serializer import AdCompleteSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

def demo_enhanced_ad_detail():
    """Demonstrate the enhanced ad detail functionality"""
    
    print("🎯 Nordic Loop Platform - Enhanced Ad Detail Demo")
    print("=" * 60)
    
    # Find a complete ad
    complete_ads = Ad.objects.filter(is_complete=True).order_by('-updated_at')
    
    if not complete_ads.exists():
        print("❌ No complete ads found. Please create some test data first.")
        return
    
    # Get the most recent complete ad
    ad = complete_ads.first()
    
    print(f"📋 Demonstrating with Ad ID: {ad.id}")
    print(f"📝 Title: {ad.title}")
    print("-" * 60)
    
    # Serialize the ad with all enhanced information
    serializer = AdCompleteSerializer(ad)
    data = serializer.data
    
    # Display key enhanced features
    print("\n🏢 COMPANY INFORMATION:")
    print(f"   Company Name: {data.get('company_name', 'N/A')}")
    print(f"   Posted By: {data.get('posted_by', 'N/A')}")
    
    print("\n📦 MATERIAL DETAILS:")
    print(f"   Category: {data.get('category_name', 'N/A')}")
    print(f"   Subcategory: {data.get('subcategory_name', 'N/A')}")
    print(f"   Packaging: {data.get('packaging_display', 'N/A')} ({data.get('packaging', 'N/A')})")
    print(f"   Frequency: {data.get('material_frequency_display', 'N/A')}")
    print(f"   Origin: {data.get('origin_display', 'N/A')}")
    print(f"   Contamination: {data.get('contamination_display', 'N/A')}")
    print(f"   Additives: {data.get('additives_display', 'N/A')}")
    print(f"   Storage: {data.get('storage_conditions_display', 'N/A')}")
    
    print("\n🔧 PROCESSING & LOGISTICS:")
    processing_methods = data.get('processing_methods_display', [])
    if processing_methods:
        print(f"   Processing Methods: {', '.join(processing_methods)}")
    else:
        print("   Processing Methods: Not specified")
    
    delivery_options = data.get('delivery_options_display', [])
    if delivery_options:
        print(f"   Delivery Options: {', '.join(delivery_options)}")
    else:
        print("   Delivery Options: Not specified")
    
    print(f"   Pickup Available: {'Yes' if data.get('pickup_available') else 'No'}")
    print(f"   Location: {data.get('location_summary', 'Not specified')}")
    
    print("\n💰 PRICING & QUANTITY:")
    print(f"   Available Quantity: {data.get('available_quantity', 'N/A')} {data.get('unit_of_measurement_display', '')}")
    print(f"   Minimum Order: {data.get('minimum_order_quantity', 'N/A')} {data.get('unit_of_measurement_display', '')}")
    print(f"   Starting Bid Price: {data.get('starting_bid_price', 'N/A')} {data.get('currency_display', '')}")
    if data.get('reserve_price'):
        print(f"   Reserve Price: {data.get('reserve_price')} {data.get('currency_display', '')}")
    print(f"   Total Starting Value: {data.get('total_starting_value', 'N/A')} {data.get('currency_display', '')}")
    
    print("\n⏰ AUCTION STATUS:")
    print(f"   Status: {data.get('auction_status', 'N/A')}")
    print(f"   Duration: {data.get('auction_duration_display', 'N/A')}")
    if data.get('time_remaining'):
        print(f"   Time Remaining: {data.get('time_remaining')}")
    else:
        print("   Time Remaining: Not active")
    
    print("\n📊 COMPLETION STATUS:")
    step_status = data.get('step_completion_status', {})
    completed_steps = sum(1 for completed in step_status.values() if completed)
    total_steps = len(step_status)
    print(f"   Steps Completed: {completed_steps}/{total_steps}")
    print(f"   Is Complete: {'Yes' if data.get('is_complete') else 'No'}")
    print(f"   Current Step: {data.get('current_step', 'N/A')}")
    
    if data.get('material_image'):
        print(f"\n🖼️  IMAGE: {data.get('material_image')}")
    
    # Show raw and display value comparison
    print("\n🔄 RAW vs DISPLAY VALUES COMPARISON:")
    comparisons = [
        ('packaging', 'packaging_display'),
        ('material_frequency', 'material_frequency_display'),
        ('origin', 'origin_display'),
        ('contamination', 'contamination_display'),
        ('currency', 'currency_display'),
    ]
    
    for raw_field, display_field in comparisons:
        raw_val = data.get(raw_field)
        display_val = data.get(display_field)
        if raw_val and display_val:
            print(f"   {raw_field}: '{raw_val}' → '{display_val}'")
    
    print("\n" + "=" * 60)
    print("✅ Enhanced ad detail demo completed!")
    print("\n📝 Key Benefits:")
    print("   • Complete transparency about the material/auction")
    print("   • Company name displayed (sensitive data protected)")
    print("   • Human-readable display values for all choice fields")
    print("   • Real-time auction status and timing")
    print("   • Comprehensive location and logistics information")
    print("   • Calculated values like total starting value")
    print("   • Step completion tracking for form progress")
    print("\n🌐 API Endpoint: GET /api/ads/{ad_id}/")
    print("🔐 Authentication: Bearer Token Required")

def demo_json_structure():
    """Show the JSON structure for frontend developers"""
    
    print("\n" + "=" * 60)
    print("📱 JSON STRUCTURE FOR FRONTEND DEVELOPERS")
    print("=" * 60)
    
    # Get a sample ad
    ad = Ad.objects.filter(is_complete=True).first()
    if not ad:
        print("❌ No complete ads found for JSON demo.")
        return
    
    serializer = AdCompleteSerializer(ad)
    data = serializer.data
    
    # Pretty print the JSON structure
    print(json.dumps(data, indent=2, default=str))

if __name__ == "__main__":
    demo_enhanced_ad_detail()
    
    # Ask if user wants to see the JSON structure
    response = input("\n🤔 Would you like to see the complete JSON structure? (y/N): ")
    if response.lower() in ['y', 'yes']:
        demo_json_structure()
    
    print("\n🎉 Demo completed! The enhanced ad detail endpoint is ready for frontend integration.") 