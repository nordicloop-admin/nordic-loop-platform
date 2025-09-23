#!/usr/bin/env python3
"""
Create 10 diverse auctions for seller olivierkarera2020@gmail.com
This script creates a variety of auctions with different categories, materials, and conditions.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from ads.models import Ad, Location
from category.models import Category
from django.utils import timezone

User = get_user_model()

def create_auctions():
    """Create 10 diverse auctions for the seller"""
    
    print("🏭 Creating 10 Draft Auctions for Olivier Karera")
    print("=" * 50)
    print("📝 Note: Creating as drafts since Stripe Connect setup is required for active auctions")
    
    # Get the seller
    try:
        seller = User.objects.get(email='olivierkarera2020@gmail.com')
        print(f"✅ Found seller: {seller.email} (ID: {seller.id})")
    except User.DoesNotExist:
        print("❌ Seller not found!")
        return
    
    # Get available categories
    categories = list(Category.objects.all())
    if not categories:
        print("❌ No categories found! Please create categories first.")
        return
    
    print(f"📂 Available categories: {len(categories)}")
    for cat in categories:
        print(f"   - {cat.name}")
    
    # Get available locations
    locations = list(Location.objects.all())
    if not locations:
        print("❌ No locations found! Please create locations first.")
        return
    
    print(f"📍 Available locations: {len(locations)}")
    for loc in locations:
        print(f"   - {loc}")
    
    # Auction data templates - different from the previous 20
    auction_templates = [
        {
            "title": "High-Grade Titanium Scrap - Aerospace Quality",
            "description": "Premium titanium scrap from aerospace manufacturing. Grade 2 and Grade 5 titanium pieces, perfect for high-end applications requiring superior strength-to-weight ratio.",
            "weight": "45",
            "unit": "kg",
            "starting_price": "350.00",
            "reserve_price": "450.00",
            "keywords": ["titanium", "aerospace", "high grade", "scrap", "lightweight"]
        },
        {
            "title": "Food-Grade Stainless Steel Containers",
            "description": "Collection of food-grade stainless steel containers from food processing industry. Various sizes, all sanitized and ready for reuse in food applications.",
            "weight": "120",
            "unit": "kg", 
            "starting_price": "85.00",
            "reserve_price": "120.00",
            "keywords": ["stainless steel", "food grade", "containers", "processing", "sanitized"]
        },
        {
            "title": "Recycled Carbon Fiber Waste - Automotive",
            "description": "Carbon fiber waste from automotive manufacturing. High-strength material suitable for composite applications, sporting goods, or specialized manufacturing.",
            "weight": "25",
            "unit": "kg",
            "starting_price": "280.00", 
            "reserve_price": "380.00",
            "keywords": ["carbon fiber", "automotive", "high strength", "composite", "manufacturing"]
        },
        {
            "title": "Premium Hardwood Lumber - Oak & Mahogany",
            "description": "Reclaimed premium hardwood lumber including oak and mahogany planks. Kiln-dried and ready for high-end furniture making or luxury construction projects.",
            "weight": "300",
            "unit": "kg",
            "starting_price": "120.00",
            "reserve_price": "180.00", 
            "keywords": ["hardwood", "oak", "mahogany", "lumber", "premium"]
        },
        {
            "title": "Industrial Hemp Fiber Bales",
            "description": "Organic hemp fiber bales perfect for textile manufacturing, insulation, or composite materials. Sustainably sourced and processed for various applications.",
            "weight": "200",
            "unit": "kg",
            "starting_price": "65.00",
            "reserve_price": "95.00",
            "keywords": ["hemp", "fiber", "organic", "sustainable", "textile"]
        },
        {
            "title": "Rare Earth Metal Components",
            "description": "Collection of rare earth metal components extracted from electronics. Contains neodymium, europium, and other valuable elements perfect for specialized applications.",
            "weight": "8",
            "unit": "kg", 
            "starting_price": "450.00",
            "reserve_price": "650.00",
            "keywords": ["rare earth", "metals", "electronics", "neodymium", "valuable"]
        },
        {
            "title": "Pharmaceutical Glass Vials - Clean",
            "description": "Clean pharmaceutical-grade glass vials from medical manufacturing. Borosilicate glass, various sizes, perfect for laboratory or pharmaceutical use.",
            "weight": "60",
            "unit": "kg",
            "starting_price": "95.00", 
            "reserve_price": "140.00",
            "keywords": ["pharmaceutical", "glass", "vials", "borosilicate", "medical"]
        },
        {
            "title": "Recycled Magnesium Alloy Sheets",
            "description": "Lightweight magnesium alloy sheets from aerospace applications. Excellent strength-to-weight ratio, perfect for specialized lightweight construction.",
            "weight": "80",
            "unit": "kg",
            "starting_price": "220.00",
            "reserve_price": "320.00",
            "keywords": ["magnesium", "alloy", "lightweight", "aerospace", "construction"]
        },
        {
            "title": "Organic Wool Textile Waste",
            "description": "Premium organic wool textile waste from luxury fashion manufacturing. Various colors and grades, perfect for recycling into new textile products.",
            "weight": "150",
            "unit": "kg",
            "starting_price": "75.00",
            "reserve_price": "110.00", 
            "keywords": ["organic", "wool", "textile", "luxury", "fashion"]
        },
        {
            "title": "Laboratory-Grade Silicon Wafers",
            "description": "Used silicon wafers from semiconductor testing. Various grades and sizes, suitable for research applications or silicon recovery processes.",
            "weight": "12",
            "unit": "kg",
            "starting_price": "180.00",
            "reserve_price": "260.00",
            "keywords": ["silicon", "wafers", "semiconductor", "laboratory", "research"]
        }
    ]
    
    # Create auctions
    created_count = 0
    
    for i, template in enumerate(auction_templates):
        try:
            # Random category selection
            category = random.choice(categories)
            
            # Random location selection
            location = random.choice(locations)
            
            # Random auction end time (between 5-21 days from now)
            days_ahead = random.randint(5, 21)
            end_time = timezone.now() + timedelta(days=days_ahead)
            
            # Create the auction as draft (inactive) since payment setup is required for active auctions
            auction = Ad.objects.create(
                user=seller,
                title=template["title"],
                description=template["description"],
                category=category,
                available_quantity=Decimal(template["weight"]),
                unit_of_measurement=template["unit"],
                starting_bid_price=Decimal(template["starting_price"]),
                reserve_price=Decimal(template["reserve_price"]),
                currency="EUR",  # Euro for this seller
                auction_end_date=end_time,
                auction_start_date=timezone.now(),
                location=location,
                keywords=", ".join(template["keywords"]),
                status="active",
                is_active=False,  # Keep as draft until payment setup is complete
                is_complete=True,
                current_step=8,  # Mark as completed
                packaging="baled",  # Default packaging
                material_frequency="monthly",  # Default frequency
            )
            
            created_count += 1
            print(f"✅ {created_count:2d}. Created: {auction.title[:50]}...")
            print(f"    Category: {category.name} | Weight: {template['weight']}{template['unit']} | Price: {template['starting_price']} EUR")
            print(f"    Location: {location} | Status: DRAFT | Ends: {end_time.strftime('%Y-%m-%d %H:%M')}")
            
        except Exception as e:
            print(f"❌ Error creating auction {i+1}: {e}")
    
    print(f"\n🎉 Successfully created {created_count} auctions!")
    print("📊 Summary:")
    print(f"   - Seller: {seller.email}")
    print(f"   - New auctions: {created_count}")
    print(f"   - Categories used: {len(set(Ad.objects.filter(user=seller).values_list('category__name', flat=True)))}")
    print("   - Price range: 65.00 - 650.00 EUR")
    print("   - Weight range: 8 - 300 kg")
    
    # Show seller's total auctions
    total_auctions = Ad.objects.filter(user=seller).count()
    print(f"   - Seller's total auctions: {total_auctions}")

if __name__ == "__main__":
    create_auctions()