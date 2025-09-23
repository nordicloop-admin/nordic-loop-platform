#!/usr/bin/env python3
"""
Create 20 diverse auctions for seller kareraol1@gmail.com
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
    """Create 20 diverse auctions for the seller"""
    
    print("🏭 Creating 20 Auctions for Nordic Loop Seller")
    print("=" * 50)
    
    # Get the seller
    try:
        seller = User.objects.get(email='kareraol1@gmail.com')
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
    
    # Auction data templates
    auction_templates = [
        {
            "title": "Premium Recycled Steel Beams - Grade A",
            "description": "High-quality recycled steel beams suitable for construction projects. These beams have been professionally cleaned and tested for structural integrity. Perfect for sustainable building projects.",
            "material_type": "Steel",
            "condition": "Excellent",
            "weight": "500",
            "unit": "kg",
            "starting_price": "45.00",
            "reserve_price": "65.00",
            "keywords": ["steel", "construction", "beams", "recycled", "sustainable"]
        },
        {
            "title": "Reclaimed Copper Wire Bundle",
            "description": "Clean copper wire recovered from electrical installations. Excellent conductivity, perfect for electrical projects or copper recycling.",
            "material_type": "Copper",
            "condition": "Good",
            "weight": "25",
            "unit": "kg",
            "starting_price": "180.00",
            "reserve_price": "220.00",
            "keywords": ["copper", "wire", "electrical", "conductor", "metal"]
        },
        {
            "title": "Industrial Aluminum Sheets - Various Sizes",
            "description": "Collection of aluminum sheets from manufacturing processes. Different thicknesses available. Great for metalworking and fabrication projects.",
            "material_type": "Aluminum",
            "condition": "Good",
            "weight": "150",
            "unit": "kg",
            "starting_price": "35.00",
            "reserve_price": "50.00",
            "keywords": ["aluminum", "sheets", "manufacturing", "fabrication", "lightweight"]
        },
        {
            "title": "Recycled Plastic Pellets - HDPE Grade",
            "description": "High-density polyethylene pellets ready for reprocessing. Sourced from clean industrial waste. Perfect for plastic manufacturing.",
            "material_type": "Plastic",
            "condition": "Excellent",
            "weight": "100",
            "unit": "kg",
            "starting_price": "25.00",
            "reserve_price": "40.00",
            "keywords": ["plastic", "HDPE", "pellets", "recycling", "manufacturing"]
        },
        {
            "title": "Mixed Electronic Components Lot",
            "description": "Assorted electronic components including resistors, capacitors, and circuit boards. Perfect for electronics recycling or component harvesting.",
            "material_type": "Electronics",
            "condition": "Fair",
            "weight": "10",
            "unit": "kg",
            "starting_price": "75.00",
            "reserve_price": "120.00",
            "keywords": ["electronics", "components", "circuit", "recycling", "precious metals"]
        },
        {
            "title": "Reclaimed Wood Planks - Oak & Pine Mix",
            "description": "Beautiful reclaimed wood planks from demolished buildings. Mix of oak and pine, perfect for furniture making or rustic projects.",
            "material_type": "Wood",
            "condition": "Good",
            "weight": "200",
            "unit": "kg",
            "starting_price": "60.00",
            "reserve_price": "85.00",
            "keywords": ["wood", "reclaimed", "oak", "pine", "furniture"]
        },
        {
            "title": "Stainless Steel Appliance Parts",
            "description": "Collection of stainless steel parts from appliance manufacturing. High-grade steel suitable for various applications.",
            "material_type": "Steel",
            "condition": "Excellent",
            "weight": "75",
            "unit": "kg",
            "starting_price": "55.00",
            "reserve_price": "80.00",
            "keywords": ["stainless steel", "appliance", "manufacturing", "corrosion resistant"]
        },
        {
            "title": "Brass Fittings and Pipes Collection",
            "description": "Assorted brass fittings and pipe sections from plumbing installations. High-quality brass with excellent corrosion resistance.",
            "material_type": "Brass",
            "condition": "Good",
            "weight": "40",
            "unit": "kg",
            "starting_price": "95.00",
            "reserve_price": "130.00",
            "keywords": ["brass", "plumbing", "fittings", "pipes", "corrosion resistant"]
        },
        {
            "title": "Recycled Cardboard Bales - Clean Grade",
            "description": "Clean cardboard bales ready for recycling. Sourced from retail packaging. Perfect for paper mills or cardboard manufacturing.",
            "material_type": "Cardboard",
            "condition": "Excellent",
            "weight": "500",
            "unit": "kg",
            "starting_price": "15.00",
            "reserve_price": "25.00",
            "keywords": ["cardboard", "packaging", "paper", "recycling", "sustainable"]
        },
        {
            "title": "Glass Cullet - Mixed Colors",
            "description": "Clean glass cullet in mixed colors. Perfect for glass manufacturing or artistic projects. All glass has been cleaned and sorted.",
            "material_type": "Glass",
            "condition": "Good",
            "weight": "300",
            "unit": "kg",
            "starting_price": "20.00",
            "reserve_price": "35.00",
            "keywords": ["glass", "cullet", "recycling", "manufacturing", "artistic"]
        },
        {
            "title": "Industrial Rubber Sheets - EPDM Grade",
            "description": "High-quality EPDM rubber sheets from industrial applications. Weather-resistant and durable. Great for sealing applications.",
            "material_type": "Rubber",
            "condition": "Excellent",
            "weight": "80",
            "unit": "kg",
            "starting_price": "45.00",
            "reserve_price": "65.00",
            "keywords": ["rubber", "EPDM", "industrial", "weather resistant", "sealing"]
        },
        {
            "title": "Textile Fabric Offcuts - Cotton Blend",
            "description": "High-quality cotton blend fabric offcuts from textile manufacturing. Various colors and patterns available.",
            "material_type": "Textile",
            "condition": "Excellent",
            "weight": "50",
            "unit": "kg",
            "starting_price": "30.00",
            "reserve_price": "50.00",
            "keywords": ["textile", "fabric", "cotton", "manufacturing", "offcuts"]
        },
        {
            "title": "Lead-Free Solder Wire Spools",
            "description": "Professional grade lead-free solder wire on spools. Perfect for electronics manufacturing and repair work.",
            "material_type": "Metal Alloy",
            "condition": "Excellent",
            "weight": "5",
            "unit": "kg",
            "starting_price": "120.00",
            "reserve_price": "160.00",
            "keywords": ["solder", "electronics", "lead-free", "manufacturing", "repair"]
        },
        {
            "title": "PVC Pipe Offcuts - Various Diameters",
            "description": "Collection of PVC pipe offcuts in various diameters. Perfect for plumbing projects or plastic recycling.",
            "material_type": "Plastic",
            "condition": "Good",
            "weight": "120",
            "unit": "kg",
            "starting_price": "18.00",
            "reserve_price": "30.00",
            "keywords": ["PVC", "pipe", "plumbing", "construction", "plastic"]
        },
        {
            "title": "Ceramic Tile Surplus - Premium Grade",
            "description": "Premium ceramic tiles from construction surplus. Various sizes and colors. Perfect for renovation projects.",
            "material_type": "Ceramic",
            "condition": "Excellent",
            "weight": "200",
            "unit": "kg",
            "starting_price": "40.00",
            "reserve_price": "60.00",
            "keywords": ["ceramic", "tiles", "construction", "renovation", "flooring"]
        },
        {
            "title": "Battery Pack Components - Lithium",
            "description": "Lithium battery pack components from electronics manufacturing. Contains valuable lithium for recycling.",
            "material_type": "Electronics",
            "condition": "Fair",
            "weight": "15",
            "unit": "kg",
            "starting_price": "200.00",
            "reserve_price": "300.00",
            "keywords": ["battery", "lithium", "electronics", "recycling", "energy storage"]
        },
        {
            "title": "Insulation Material - Rockwool Batts",
            "description": "Clean rockwool insulation batts from construction projects. Excellent thermal and acoustic insulation properties.",
            "material_type": "Insulation",
            "condition": "Good",
            "weight": "100",
            "unit": "kg",
            "starting_price": "25.00",
            "reserve_price": "40.00",
            "keywords": ["insulation", "rockwool", "thermal", "acoustic", "construction"]
        },
        {
            "title": "Nickel-Plated Hardware Collection",
            "description": "Assorted nickel-plated hardware including bolts, nuts, and brackets. High corrosion resistance and durability.",
            "material_type": "Metal",
            "condition": "Excellent",
            "weight": "30",
            "unit": "kg",
            "starting_price": "85.00",
            "reserve_price": "120.00",
            "keywords": ["nickel", "hardware", "bolts", "corrosion resistant", "plated"]
        },
        {
            "title": "Composite Material Panels",
            "description": "Lightweight composite panels from aerospace applications. High strength-to-weight ratio, perfect for specialized projects.",
            "material_type": "Composite",
            "condition": "Excellent",
            "weight": "60",
            "unit": "kg",
            "starting_price": "150.00",
            "reserve_price": "220.00",
            "keywords": ["composite", "aerospace", "lightweight", "high strength", "panels"]
        },
        {
            "title": "Granite Countertop Offcuts",
            "description": "Beautiful granite offcuts from countertop installations. Various colors and finishes. Perfect for smaller projects.",
            "material_type": "Stone",
            "condition": "Excellent",
            "weight": "400",
            "unit": "kg",
            "starting_price": "80.00",
            "reserve_price": "120.00",
            "keywords": ["granite", "stone", "countertop", "offcuts", "natural"]
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
            
            # Random auction end time (between 3-14 days from now)
            days_ahead = random.randint(3, 14)
            end_time = timezone.now() + timedelta(days=days_ahead)
            
            # Create the auction
            auction = Ad.objects.create(
                user=seller,
                title=template["title"],
                description=template["description"],
                category=category,
                available_quantity=Decimal(template["weight"]),
                unit_of_measurement=template["unit"],
                starting_bid_price=Decimal(template["starting_price"]),
                reserve_price=Decimal(template["reserve_price"]),
                currency="SEK",  # Swedish Krona since it's a Nordic marketplace
                auction_end_date=end_time,
                auction_start_date=timezone.now(),
                location=location,  # Use Location object
                keywords=", ".join(template["keywords"]),
                status="active",
                is_active=True,
                is_complete=True,
                current_step=8,  # Mark as completed
            )
            
            created_count += 1
            print(f"✅ {created_count:2d}. Created: {auction.title[:50]}...")
            print(f"    Category: {category.name} | Weight: {template['weight']}{template['unit']} | Price: {template['starting_price']} SEK")
            print(f"    Location: {location} | Ends: {end_time.strftime('%Y-%m-%d %H:%M')}")
            
        except Exception as e:
            print(f"❌ Error creating auction {i+1}: {e}")
    
    print(f"\n🎉 Successfully created {created_count} auctions!")
    print(f"📊 Summary:")
    print(f"   - Seller: {seller.email}")
    print(f"   - Total auctions: {created_count}")
    print(f"   - Categories used: {len(set(Ad.objects.filter(user=seller).values_list('category__name', flat=True)))}")
    print(f"   - Price range: 15.00 - 300.00 SEK")
    print(f"   - Weight range: 5 - 500 kg")
    
    # Show seller's total auctions
    total_auctions = Ad.objects.filter(user=seller).count()
    print(f"   - Seller's total auctions: {total_auctions}")

if __name__ == "__main__":
    create_auctions()