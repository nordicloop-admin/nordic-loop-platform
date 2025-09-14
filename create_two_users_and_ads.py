#!/usr/bin/env python3
"""
Script to create two users for Nordic Loop Platform:
1. kareraol1@gmail.com (admin and staff) with password Cmu@2025 + some ads
2. olivierkarera2020@gmail.com (normal user) with password Krol@2027
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add the project directory to Python path
project_dir = "/home/okarera/Documents/Personal/Projects/Side Projects/Noordic Loop Market Place/nordic-loop-platform"
sys.path.append(project_dir)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from ads.models import Ad, Location
from category.models import Category, SubCategory
from company.models import Company

User = get_user_model()

def create_admin_user():
    """Create or get the admin user kareraol1@gmail.com"""
    print("👤 Creating/finding admin user...")
    
    email = "kareraol1@gmail.com"
    password = "Cmu@2025"
    
    try:
        user = User.objects.get(email=email)
        print(f"  ✅ Found existing user: {user.email}")
        # Update user to make sure they have admin privileges
        user.is_staff = True
        user.is_superuser = True
        user.role = "Admin"
        user.can_place_ads = True
        user.can_place_bids = True
        user.save()
        print(f"  🔧 Updated user privileges - Staff: {user.is_staff}, Superuser: {user.is_superuser}")
        return user
    except User.DoesNotExist:
        # Create admin user
        user = User.objects.create(
            username=email,
            email=email,
            first_name="Okello",
            last_name="Karera",
            name="Okello Karera",
            password=make_password(password),
            is_active=True,
            is_staff=True,        # Admin privilege
            is_superuser=True,    # Admin privilege
            can_place_ads=True,
            can_place_bids=True,
            role="Admin"          # Admin role
        )
        print(f"  ✅ Created new admin user: {user.email}")
        return user

def create_normal_user():
    """Create or get the normal user olivierkarera2020@gmail.com"""
    print("👤 Creating/finding normal user...")
    
    email = "olivierkarera2020@gmail.com"
    password = "Krol@2027"
    
    try:
        user = User.objects.get(email=email)
        print(f"  ✅ Found existing user: {user.email}")
        return user
    except User.DoesNotExist:
        # Create normal user
        user = User.objects.create(
            username=email,
            email=email,
            first_name="Olivier",
            last_name="Karera",
            name="Olivier Karera",
            password=make_password(password),
            is_active=True,
            is_staff=False,       # Normal user
            is_superuser=False,   # Normal user
            can_place_ads=True,
            can_place_bids=True,
            role="Staff"          # Normal user role
        )
        print(f"  ✅ Created new normal user: {user.email}")
        return user

def create_locations():
    """Create diverse locations for the ads"""
    print("📍 Creating locations...")
    
    locations_data = [
        {
            "country": "Sweden",
            "state_province": "Stockholm County", 
            "city": "Stockholm",
            "address_line": "Industrivägen 25",
            "postal_code": "11245",
            "latitude": 59.3293,
            "longitude": 18.0686
        },
        {
            "country": "Norway",
            "state_province": "Oslo",
            "city": "Oslo", 
            "address_line": "Nydalen Park 15",
            "postal_code": "0484",
            "latitude": 59.9139,
            "longitude": 10.7522
        },
        {
            "country": "Denmark",
            "state_province": "Capital Region",
            "city": "Copenhagen",
            "address_line": "Ørestads Boulevard 45",
            "postal_code": "2300",
            "latitude": 55.6761,
            "longitude": 12.5683
        },
        {
            "country": "Finland",
            "state_province": "Uusimaa",
            "city": "Helsinki",
            "address_line": "Mannerheimintie 12",
            "postal_code": "00100",
            "latitude": 60.1699,
            "longitude": 24.9384
        },
        {
            "country": "Germany",
            "state_province": "Berlin",
            "city": "Berlin",
            "address_line": "Potsdamer Platz 10",
            "postal_code": "10785",
            "latitude": 52.5200,
            "longitude": 13.4050
        }
    ]
    
    locations = []
    for loc_data in locations_data:
        location, created = Location.objects.get_or_create(
            city=loc_data["city"],
            country=loc_data["country"],
            address_line=loc_data["address_line"],
            defaults=loc_data
        )
        if created:
            print(f"  ✅ Created location: {location.city}, {location.country}")
        locations.append(location)
    
    return locations

def get_categories_and_subcategories():
    """Get available categories and subcategories"""
    print("🏷️ Getting categories...")
    
    categories = Category.objects.all()
    
    category_data = []
    for category in categories:
        subcategories = list(category.subcategories.all())
        if subcategories:
            category_data.append({
                'category': category,
                'subcategories': subcategories
            })
    
    # If no categories exist, create some default ones
    if not category_data:
        print("  🔧 No categories found, creating default ones...")
        
        # Create Metals category
        metals_category, created = Category.objects.get_or_create(
            name="Metals"
        )
        
        # Create subcategories for Metals
        aluminum_sub, _ = SubCategory.objects.get_or_create(
            name="Aluminum",
            category=metals_category
        )
        copper_sub, _ = SubCategory.objects.get_or_create(
            name="Copper",
            category=metals_category
        )
        steel_sub, _ = SubCategory.objects.get_or_create(
            name="Steel",
            category=metals_category
        )
        
        category_data.append({
            'category': metals_category,
            'subcategories': [aluminum_sub, copper_sub, steel_sub]
        })
        
        # Create Textiles category
        textiles_category, created = Category.objects.get_or_create(
            name="Textiles"
        )
        
        cotton_sub, _ = SubCategory.objects.get_or_create(
            name="Cotton",
            category=textiles_category
        )
        polyester_sub, _ = SubCategory.objects.get_or_create(
            name="Polyester",
            category=textiles_category
        )
        
        category_data.append({
            'category': textiles_category,
            'subcategories': [cotton_sub, polyester_sub]
        })
    
    print(f"  ✅ Found/Created {len(category_data)} categories")
    return category_data

def create_ads_for_admin_user(user, locations, category_data):
    """Create diverse ads for the admin user"""
    print(f"🏭 Creating ads for {user.email}...")
    
    ads_data = [
        {
            "title": "Premium Aluminum Scrap - Aerospace Grade",
            "description": "High-quality aluminum scrap from aerospace manufacturing. Clean, sorted, and ready for high-end recycling applications. Perfect for aluminum foundries requiring premium materials.",
            "specific_material": "7075-T6 Aerospace Aluminum",
            "available_quantity": 350,
            "unit_of_measurement": "kg",
            "minimum_order_quantity": 50,
            "starting_bid_price": 2.15,
            "reserve_price": 2.65,
            "packaging": "baled",
            "material_frequency": "monthly",
            "origin": "post_industrial",
            "contamination": "clean",
            "additives": ["no_additives"],
            "storage_conditions": "climate_controlled",
            "processing_methods": ["mechanical_recycling"],
            "keywords": "aluminum, aerospace, 7075, premium, foundry, recycling"
        },
        {
            "title": "High-Purity Copper Wire - Electronics Grade",
            "description": "Ultra-pure copper wire reclaimed from high-end electronics manufacturing. 99.99% purity, perfect for precision applications and high-grade copper smelting.",
            "specific_material": "99.99% Pure Copper Wire",
            "available_quantity": 220,
            "unit_of_measurement": "kg",
            "minimum_order_quantity": 30,
            "starting_bid_price": 7.80,
            "reserve_price": 8.50,
            "packaging": "big_bag",
            "material_frequency": "weekly",
            "origin": "post_industrial",
            "contamination": "clean",
            "additives": ["no_additives"],
            "storage_conditions": "climate_controlled",
            "processing_methods": ["mechanical_recycling"],
            "keywords": "copper, wire, electronics, ultra-pure, smelting, precision"
        },
        {
            "title": "Structural Steel Beams - Construction Grade",
            "description": "Heavy-duty structural steel beams from commercial building demolition. Various sizes available, ranging from 200mm to 600mm height. Ideal for construction projects and steel fabrication.",
            "specific_material": "S355JR Structural Steel Beams",
            "available_quantity": 25,
            "unit_of_measurement": "tonnes",
            "minimum_order_quantity": 3,
            "starting_bid_price": 420.00,
            "reserve_price": 480.00,
            "packaging": "loose",
            "material_frequency": "one_time",
            "origin": "post_consumer",
            "contamination": "slightly_contaminated",
            "additives": ["protective_coating"],
            "storage_conditions": "protected_outdoor",
            "processing_methods": ["cutting", "welding", "cleaning"],
            "keywords": "steel, beams, structural, S355JR, construction, demolition, fabrication"
        },
        {
            "title": "Food-Grade Stainless Steel Scraps",
            "description": "Premium food-grade stainless steel scraps from restaurant equipment manufacturing. 316L grade with excellent corrosion resistance, perfect for high-end recycling applications.",
            "specific_material": "316L Food-Grade Stainless Steel",
            "available_quantity": 180,
            "unit_of_measurement": "kg",
            "minimum_order_quantity": 25,
            "starting_bid_price": 2.85,
            "reserve_price": 3.35,
            "packaging": "octabin",
            "material_frequency": "bi_weekly",
            "origin": "post_industrial",
            "contamination": "clean", 
            "additives": ["no_additives"],
            "storage_conditions": "protected_outdoor",
            "processing_methods": ["mechanical_recycling"],
            "keywords": "stainless steel, 316L, food grade, restaurant, equipment, corrosion resistant"
        },
        {
            "title": "Industrial Cotton Textile Waste",
            "description": "Clean industrial cotton textile waste from garment manufacturing. Suitable for recycling into new textile products or industrial applications.",
            "specific_material": "100% Cotton Textile Waste",
            "available_quantity": 500,
            "unit_of_measurement": "kg",
            "minimum_order_quantity": 100,
            "starting_bid_price": 0.85,
            "reserve_price": 1.20,
            "packaging": "big_bag",
            "material_frequency": "weekly",
            "origin": "post_industrial",
            "contamination": "clean",
            "additives": ["no_additives"],
            "storage_conditions": "protected_outdoor",
            "processing_methods": ["mechanical_recycling", "shredding"],
            "keywords": "cotton, textile, waste, garment, manufacturing, clean, recycling"
        },
        {
            "title": "Mixed Polyester Fabric Scraps",
            "description": "High-quality polyester fabric scraps from upholstery manufacturing. Various colors and weights available. Excellent for textile recycling and fiber recovery.",
            "specific_material": "Mixed Polyester Fabrics",
            "available_quantity": 320,
            "unit_of_measurement": "kg",
            "minimum_order_quantity": 50,
            "starting_bid_price": 1.25,
            "reserve_price": 1.65,
            "packaging": "baled",
            "material_frequency": "monthly",
            "origin": "post_industrial",
            "contamination": "clean",
            "additives": ["fire_retardant"],
            "storage_conditions": "climate_controlled",
            "processing_methods": ["mechanical_recycling", "chemical_recycling"],
            "keywords": "polyester, fabric, scraps, upholstery, manufacturing, fiber recovery"
        }
    ]
    
    created_ads = []
    
    for i, ad_data in enumerate(ads_data):
        # Select category and subcategory
        if category_data:
            # Try to match material type with appropriate category
            if "aluminum" in ad_data["title"].lower() or "copper" in ad_data["title"].lower() or "steel" in ad_data["title"].lower():
                # Find metals category
                metals_cat = next((cat for cat in category_data if "metal" in cat['category'].name.lower()), None)
                if metals_cat:
                    cat_info = metals_cat
                    # Try to match subcategory
                    if "aluminum" in ad_data["title"].lower():
                        subcategory = next((sub for sub in cat_info['subcategories'] if "aluminum" in sub.name.lower()), None)
                    elif "copper" in ad_data["title"].lower():
                        subcategory = next((sub for sub in cat_info['subcategories'] if "copper" in sub.name.lower()), None)
                    elif "steel" in ad_data["title"].lower():
                        subcategory = next((sub for sub in cat_info['subcategories'] if "steel" in sub.name.lower()), None)
                    else:
                        subcategory = random.choice(cat_info['subcategories'])
                else:
                    cat_info = category_data[0]
                    subcategory = random.choice(cat_info['subcategories'])
            elif "textile" in ad_data["title"].lower() or "cotton" in ad_data["title"].lower() or "polyester" in ad_data["title"].lower():
                # Find textile category
                textile_cat = next((cat for cat in category_data if "textile" in cat['category'].name.lower()), None)
                if textile_cat:
                    cat_info = textile_cat
                    # Try to match subcategory
                    if "cotton" in ad_data["title"].lower():
                        subcategory = next((sub for sub in cat_info['subcategories'] if "cotton" in sub.name.lower()), None)
                    elif "polyester" in ad_data["title"].lower():
                        subcategory = next((sub for sub in cat_info['subcategories'] if "polyester" in sub.name.lower()), None)
                    else:
                        subcategory = random.choice(cat_info['subcategories'])
                else:
                    cat_info = category_data[0]
                    subcategory = random.choice(cat_info['subcategories'])
            else:
                cat_info = category_data[i % len(category_data)]
                subcategory = random.choice(cat_info['subcategories'])
                
            category = cat_info['category']
        else:
            # Fallback
            category, _ = Category.objects.get_or_create(name="General")
            subcategory, _ = SubCategory.objects.get_or_create(
                name="Mixed Materials",
                category=category
            )
            
        location = locations[i % len(locations)]
        
        # Create auction dates
        auction_start = timezone.now() + timedelta(hours=random.randint(1, 48))
        auction_end = auction_start + timedelta(days=random.randint(5, 14))
        
        try:
            ad = Ad.objects.create(
                user=user,
                
                # Step 1: Material Type
                category=category,
                subcategory=subcategory,
                specific_material=ad_data["specific_material"],
                packaging=ad_data["packaging"],
                material_frequency=ad_data["material_frequency"],
                
                # Step 2: Specifications  
                additional_specifications=f"High-quality {ad_data['specific_material']} suitable for professional applications",
                
                # Step 3: Material Origin
                origin=ad_data["origin"],
                
                # Step 4: Contamination
                contamination=ad_data["contamination"],
                additives=ad_data["additives"],
                storage_conditions=ad_data["storage_conditions"],
                
                # Step 5: Processing Methods
                processing_methods=ad_data["processing_methods"],
                
                # Step 6: Location & Logistics
                location=location,
                pickup_available=True,
                delivery_options=["pickup", "delivery"],
                
                # Step 7: Quantity & Pricing
                available_quantity=ad_data["available_quantity"],
                unit_of_measurement=ad_data["unit_of_measurement"], 
                minimum_order_quantity=ad_data["minimum_order_quantity"],
                starting_bid_price=Decimal(str(ad_data["starting_bid_price"])),
                currency="EUR",
                auction_duration=random.randint(7, 14),
                reserve_price=Decimal(str(ad_data["reserve_price"])),
                
                # Step 8: Title, Description & Image
                title=ad_data["title"],
                description=ad_data["description"],
                keywords=ad_data["keywords"],
                
                # System fields
                is_active=True,
                status="active",
                current_step=8,
                is_complete=True,
                auction_start_date=auction_start,
                auction_end_date=auction_end,
                allow_broker_bids=True
            )
            
            created_ads.append(ad)
            print(f"  ✅ Created ad #{ad.id}: {ad.title}")
            
        except Exception as e:
            print(f"  ❌ Error creating ad {i+1}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return created_ads

def main():
    """Main function to create users and ads"""
    print("🚀 Starting Nordic Loop - Creating Two Users and Ads...")
    print("=" * 70)
    
    try:
        # Step 1: Create admin user
        admin_user = create_admin_user()
        
        # Step 2: Create normal user
        normal_user = create_normal_user()
        
        # Step 3: Create locations
        locations = create_locations()
        
        # Step 4: Get/create categories
        category_data = get_categories_and_subcategories()
        
        # Step 5: Create ads for admin user
        ads = create_ads_for_admin_user(admin_user, locations, category_data)
        
        print("=" * 70)
        print(f"🎉 SUCCESS! Created:")
        print(f"   👤 Admin User: {admin_user.email} (Staff: {admin_user.is_staff}, Superuser: {admin_user.is_superuser})")
        print(f"   👤 Normal User: {normal_user.email} (Staff: {normal_user.is_staff}, Superuser: {normal_user.is_superuser})")
        print(f"   📍 Locations: {len(locations)}")
        print(f"   🏭 Ads: {len(ads)}")
        print("=" * 70)
        
        print(f"\n📋 Created Ads Summary for {admin_user.email}:")
        for ad in ads:
            print(f"   • #{ad.id}: {ad.title}")
            print(f"     Category: {ad.category.name} > {ad.subcategory.name}")
            print(f"     Location: {ad.location.city}, {ad.location.country}")
            print(f"     Starting Price: €{ad.starting_bid_price}/{ad.unit_of_measurement}")
            print(f"     Quantity: {ad.available_quantity} {ad.unit_of_measurement}")
            print(f"     Auction End: {ad.auction_end_date.strftime('%Y-%m-%d %H:%M')}")
            print()
        
        print("🔐 Login Credentials:")
        print(f"   📧 Admin User:")
        print(f"      Email: kareraol1@gmail.com")
        print(f"      Password: Cmu@2025")
        print(f"      Role: Admin (can access admin panels)")
        print()
        print(f"   📧 Normal User:")
        print(f"      Email: olivierkarera2020@gmail.com")
        print(f"      Password: Krol@2027") 
        print(f"      Role: Regular User")
        print()
        print("✨ Both users can now access the Nordic Loop marketplace!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
