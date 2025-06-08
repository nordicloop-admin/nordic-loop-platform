#!/usr/bin/env python
"""
Additional Ads Creation Script for Nordic Loop Platform
Creates 10 additional diverse auction ads for expanded testing and demonstration
"""

import os
import sys
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from category.models import Category, SubCategory
from company.models import Company
from ads.models import Ad, Location
from bids.models import Bid

User = get_user_model()

def create_additional_locations():
    """Create additional locations for the new ads"""
    print("📍 Creating additional locations...")
    
    additional_locations_data = [
        {
            "country": "Sweden",
            "state_province": "Uppsala County",
            "city": "Uppsala",
            "address_line": "Industrigatan 22",
            "postal_code": "75237",
            "latitude": 59.8586,
            "longitude": 17.6389
        },
        {
            "country": "Sweden", 
            "state_province": "Östergötland County",
            "city": "Linköping",
            "address_line": "Teknologgatan 8",
            "postal_code": "58330",
            "latitude": 58.4108,
            "longitude": 15.6214
        },
        {
            "country": "Finland",
            "state_province": "Uusimaa",
            "city": "Helsinki",
            "address_line": "Teollisuuskatu 12",
            "postal_code": "00510",
            "latitude": 60.1699,
            "longitude": 24.9384
        },
        {
            "country": "Sweden",
            "state_province": "Halland County",
            "city": "Halmstad",
            "address_line": "Industripark 5",
            "postal_code": "30233",
            "latitude": 56.6745,
            "longitude": 12.8581
        },
        {
            "country": "Norway",
            "state_province": "Rogaland",
            "city": "Stavanger",
            "address_line": "Petroleumsveien 44",
            "postal_code": "4056",
            "latitude": 58.9700,
            "longitude": 5.7331
        }
    ]
    
    created_locations = []
    for loc_data in additional_locations_data:
        location, created = Location.objects.get_or_create(
            city=loc_data["city"],
            country=loc_data["country"],
            defaults=loc_data
        )
        if created:
            print(f"  ✅ Created location: {location}")
        created_locations.append(location)
    
    return created_locations

def create_additional_ads():
    """Create 10 additional diverse auction ads"""
    print("🏭 Creating 10 additional material ads...")
    
    # Get required data
    users = list(User.objects.all())
    if not users:
        print("❌ No users found. Please run setup_test_data.py first.")
        return []
    
    # Get existing and new locations
    all_locations = list(Location.objects.all())
    additional_locations = create_additional_locations()
    all_locations.extend(additional_locations)
    
    # Get categories and subcategories
    try:
        plastics_cat = Category.objects.get(name="Plastics")
        paper_cat = Category.objects.get(name="Paper")
        metals_cat = Category.objects.get(name="Metals")
        glass_cat = Category.objects.get(name="Glass")
        textiles_cat = Category.objects.get(name="Textiles")
        
        # Plastic subcategories
        ldpe_subcat = SubCategory.objects.get(name="LDPE", category=plastics_cat)
        ps_subcat = SubCategory.objects.get(name="PS", category=plastics_cat)
        pvc_subcat = SubCategory.objects.get(name="PVC", category=plastics_cat)
        other_plastic_subcat = SubCategory.objects.get(name="Other", category=plastics_cat)
        
        # Paper subcategories
        office_paper_subcat = SubCategory.objects.get(name="Office Paper", category=paper_cat)
        newspaper_subcat = SubCategory.objects.get(name="Newspaper", category=paper_cat)
        mixed_paper_subcat = SubCategory.objects.get(name="Mixed Paper", category=paper_cat)
        
        # Metal subcategories
        steel_subcat = SubCategory.objects.get(name="Steel", category=metals_cat)
        copper_subcat = SubCategory.objects.get(name="Copper", category=metals_cat)
        mixed_metals_subcat = SubCategory.objects.get(name="Mixed Metals", category=metals_cat)
        
        # Glass subcategories
        clear_glass_subcat = SubCategory.objects.get(name="Clear Glass", category=glass_cat)
        colored_glass_subcat = SubCategory.objects.get(name="Colored Glass", category=glass_cat)
        
        # Textile subcategories
        cotton_subcat = SubCategory.objects.get(name="Cotton", category=textiles_cat)
        
    except Exception as e:
        print(f"❌ Error getting categories/subcategories: {e}")
        print("Please run setup_test_data.py first to create categories.")
        return []
    
    additional_ads_data = [
        {
            # LDPE Film
            "category": plastics_cat,
            "subcategory": ldpe_subcat,
            "specific_material": "LDPE stretch film from packaging industry",
            "packaging": "roles",
            "material_frequency": "weekly",
            
            "additional_specifications": "Clear LDPE film, 20-50 micron thickness, minimal contamination, used for pallet wrapping",
            
            "origin": "post_industrial",
            
            "contamination": "slightly_contaminated",
            "additives": "no_additives",
            "storage_conditions": "protected_outdoor",
            
            "processing_methods": ["extrusion", "blow_moulding"],
            
            "location": all_locations[0] if all_locations else None,
            "pickup_available": True,
            "delivery_options": ["pickup_only", "local_delivery"],
            
            "available_quantity": Decimal("85.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("8.00"),
            "starting_bid_price": Decimal("720.00"),
            "currency": "EUR",
            "auction_duration": 7,
            "reserve_price": Decimal("820.00"),
            
            "title": "LDPE Stretch Film - Industrial Packaging Waste",
            "description": "High-quality LDPE stretch film from packaging operations. Clean material with minimal contamination, perfect for recycling into new film products. Weekly collection available.",
            "keywords": "LDPE, stretch film, packaging, industrial, recycling"
        },
        {
            # Polystyrene Foam
            "category": plastics_cat,
            "subcategory": ps_subcat,
            "specific_material": "Expanded polystyrene (EPS) foam packaging",
            "packaging": "loose",
            "material_frequency": "monthly",
            
            "additional_specifications": "White EPS foam, various densities, clean packaging material, food-grade origin",
            
            "origin": "post_consumer",
            
            "contamination": "clean",
            "additives": "flame_retardants",
            "storage_conditions": "climate_controlled",
            
            "processing_methods": ["sintering", "extrusion"],
            
            "location": all_locations[1] if len(all_locations) > 1 else all_locations[0],
            "pickup_available": False,
            "delivery_options": ["national_shipping", "freight_forwarding"],
            
            "available_quantity": Decimal("25.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("2.00"),
            "starting_bid_price": Decimal("450.00"),
            "currency": "EUR",
            "auction_duration": 14,
            "reserve_price": Decimal("550.00"),
            
            "title": "EPS Foam Packaging - Food Grade Quality",
            "description": "Clean expanded polystyrene foam from food packaging industry. Excellent quality material suitable for recycling into new foam products or alternative applications.",
            "keywords": "EPS, polystyrene, foam, packaging, food grade"
        },
        {
            # PVC Pipe Waste
            "category": plastics_cat,
            "subcategory": pvc_subcat,
            "specific_material": "PVC pipe offcuts and construction waste",
            "packaging": "container",
            "material_frequency": "quarterly",
            
            "additional_specifications": "Mixed PVC pipes, various diameters, construction grade, some fittings included",
            
            "origin": "post_industrial",
            
            "contamination": "slightly_contaminated",
            "additives": "chlorides",
            "storage_conditions": "unprotected_outdoor",
            
            "processing_methods": ["extrusion", "calendering"],
            
            "location": all_locations[2] if len(all_locations) > 2 else all_locations[0],
            "pickup_available": True,
            "delivery_options": ["pickup_only", "local_delivery", "national_shipping"],
            
            "available_quantity": Decimal("120.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("15.00"),
            "starting_bid_price": Decimal("380.00"),
            "currency": "EUR",
            "auction_duration": 30,
            "reserve_price": Decimal("450.00"),
            
            "title": "PVC Construction Waste - Pipe and Fittings",
            "description": "PVC construction waste including pipes and fittings from building projects. Good for recycling into new PVC products. Quarterly large batch availability.",
            "keywords": "PVC, pipes, construction, building, recycling"
        },
        {
            # Mixed Plastic Waste
            "category": plastics_cat,
            "subcategory": other_plastic_subcat,
            "specific_material": "Mixed plastic waste from electronics industry",
            "packaging": "big_bag",
            "material_frequency": "bi_weekly",
            
            "additional_specifications": "Mixed plastics: ABS, PC, PA, sorted by color, electronics housing waste",
            
            "origin": "post_industrial",
            
            "contamination": "clean",
            "additives": "flame_retardants",
            "storage_conditions": "climate_controlled",
            
            "processing_methods": ["injection_moulding", "extrusion"],
            
            "location": all_locations[3] if len(all_locations) > 3 else all_locations[0],
            "pickup_available": True,
            "delivery_options": ["local_delivery", "national_shipping", "international_shipping"],
            
            "available_quantity": Decimal("45.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("3.00"),
            "starting_bid_price": Decimal("1100.00"),
            "currency": "EUR",
            "auction_duration": 7,
            "reserve_price": Decimal("1250.00"),
            
            "title": "Mixed Engineering Plastics - Electronics Waste",
            "description": "High-value mixed engineering plastics from electronics manufacturing. Including ABS, PC, and PA materials. Sorted by color and clean condition.",
            "keywords": "engineering plastics, ABS, PC, PA, electronics, high value"
        },
        {
            # Office Paper
            "category": paper_cat,
            "subcategory": office_paper_subcat,
            "specific_material": "White office paper, printed documents",
            "packaging": "baled",
            "material_frequency": "weekly",
            
            "additional_specifications": "A4 and A3 white paper, printed with standard inks, minimal contamination",
            
            "origin": "post_consumer",
            
            "contamination": "slightly_contaminated",
            "additives": "no_additives",
            "storage_conditions": "protected_outdoor",
            
            "processing_methods": ["calendering"],
            
            "location": all_locations[4] if len(all_locations) > 4 else all_locations[0],
            "pickup_available": True,
            "delivery_options": ["pickup_only", "local_delivery"],
            
            "available_quantity": Decimal("60.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("5.00"),
            "starting_bid_price": Decimal("220.00"),
            "currency": "EUR",
            "auction_duration": 5,
            "reserve_price": Decimal("280.00"),
            
            "title": "White Office Paper - Weekly Collection",
            "description": "Clean white office paper from corporate offices. Regular weekly collection ensures consistent supply. Perfect for recycling into new paper products.",
            "keywords": "office paper, white paper, documents, weekly, recycling"
        },
        {
            # Newspaper
            "category": paper_cat,
            "subcategory": newspaper_subcat,
            "specific_material": "Newspaper and newsprint materials",
            "packaging": "baled",
            "material_frequency": "bi_weekly",
            
            "additional_specifications": "Mixed newspapers, newsprint, some magazines, standard newspaper ink",
            
            "origin": "post_consumer",
            
            "contamination": "clean",
            "additives": "no_additives",
            "storage_conditions": "protected_outdoor",
            
            "processing_methods": ["calendering"],
            
            "location": all_locations[0] if all_locations else None,
            "pickup_available": True,
            "delivery_options": ["pickup_only", "local_delivery", "national_shipping"],
            
            "available_quantity": Decimal("180.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("12.00"),
            "starting_bid_price": Decimal("165.00"),
            "currency": "EUR",
            "auction_duration": 10,
            "reserve_price": Decimal("200.00"),
            
            "title": "Newspaper and Newsprint - Bi-weekly Supply",
            "description": "High-volume newspaper collection from distribution centers. Clean newsprint material perfect for recycling. Consistent bi-weekly availability.",
            "keywords": "newspaper, newsprint, print media, recycling, paper"
        },
        {
            # Steel Scrap
            "category": metals_cat,
            "subcategory": steel_subcat,
            "specific_material": "Steel scrap from automotive industry",
            "packaging": "loose",
            "material_frequency": "monthly",
            
            "additional_specifications": "Mixed steel scrap, car body parts, various thicknesses, some rust present",
            
            "origin": "post_industrial",
            
            "contamination": "slightly_contaminated",
            "additives": "no_additives",
            "storage_conditions": "unprotected_outdoor",
            
            "processing_methods": ["sintering"],
            
            "location": all_locations[1] if len(all_locations) > 1 else all_locations[0],
            "pickup_available": True,
            "delivery_options": ["pickup_only", "freight_forwarding"],
            
            "available_quantity": Decimal("500.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("50.00"),
            "starting_bid_price": Decimal("320.00"),
            "currency": "EUR",
            "auction_duration": 14,
            "reserve_price": Decimal("380.00"),
            
            "title": "Automotive Steel Scrap - Large Volume",
            "description": "Large volume steel scrap from automotive manufacturing. Mixed steel types and thicknesses. Perfect for steel recycling operations.",
            "keywords": "steel, automotive, scrap metal, manufacturing, recycling"
        },
        {
            # Copper Wire
            "category": metals_cat,
            "subcategory": copper_subcat,
            "specific_material": "Copper wire and electrical components",
            "packaging": "container",
            "material_frequency": "monthly",
            
            "additional_specifications": "Mixed copper wire, electrical cables, some insulation attached, various grades",
            
            "origin": "post_industrial",
            
            "contamination": "slightly_contaminated",
            "additives": "no_additives",
            "storage_conditions": "protected_outdoor",
            
            "processing_methods": ["sintering"],
            
            "location": all_locations[2] if len(all_locations) > 2 else all_locations[0],
            "pickup_available": False,
            "delivery_options": ["national_shipping", "international_shipping"],
            
            "available_quantity": Decimal("15.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("1.00"),
            "starting_bid_price": Decimal("6500.00"),
            "currency": "EUR",
            "auction_duration": 7,
            "reserve_price": Decimal("7200.00"),
            
            "title": "Copper Wire and Electrical Components",
            "description": "High-value copper wire and electrical components from industrial operations. Mixed grades with some insulation. Excellent for copper recovery.",
            "keywords": "copper, wire, electrical, components, high value, recycling"
        },
        {
            # Clear Glass Bottles
            "category": glass_cat,
            "subcategory": clear_glass_subcat,
            "specific_material": "Clear glass bottles from beverage industry",
            "packaging": "container",
            "material_frequency": "weekly",
            
            "additional_specifications": "Clear glass bottles, various sizes, labels removed, beverage grade quality",
            
            "origin": "post_consumer",
            
            "contamination": "clean",
            "additives": "no_additives",
            "storage_conditions": "protected_outdoor",
            
            "processing_methods": ["sintering"],
            
            "location": all_locations[3] if len(all_locations) > 3 else all_locations[0],
            "pickup_available": True,
            "delivery_options": ["pickup_only", "local_delivery", "national_shipping"],
            
            "available_quantity": Decimal("80.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("8.00"),
            "starting_bid_price": Decimal("95.00"),
            "currency": "EUR",
            "auction_duration": 7,
            "reserve_price": Decimal("120.00"),
            
            "title": "Clear Glass Bottles - Beverage Grade",
            "description": "High-quality clear glass bottles from beverage collection. Clean, sorted material with labels removed. Weekly collection from distribution centers.",
            "keywords": "clear glass, bottles, beverage, recycling, weekly"
        },
        {
            # Cotton Textile Waste
            "category": textiles_cat,
            "subcategory": cotton_subcat,
            "specific_material": "Cotton textile waste from garment industry",
            "packaging": "baled",
            "material_frequency": "monthly",
            
            "additional_specifications": "Mixed cotton fabrics, various colors, garment offcuts, natural cotton only",
            
            "origin": "post_industrial",
            
            "contamination": "clean",
            "additives": "no_additives",
            "storage_conditions": "climate_controlled",
            
            "processing_methods": ["calendering"],
            
            "location": all_locations[4] if len(all_locations) > 4 else all_locations[0],
            "pickup_available": True,
            "delivery_options": ["local_delivery", "national_shipping", "international_shipping"],
            
            "available_quantity": Decimal("35.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("2.00"),
            "starting_bid_price": Decimal("1200.00"),
            "currency": "EUR",
            "auction_duration": 14,
            "reserve_price": Decimal("1400.00"),
            
            "title": "Cotton Textile Waste - Garment Industry",
            "description": "Premium cotton textile waste from garment manufacturing. Various colors and fabric weights. Perfect for textile recycling and upcycling projects.",
            "keywords": "cotton, textile, garment, fashion, recycling, upcycling"
        }
    ]
    
    created_ads = []
    
    for i, ad_data in enumerate(additional_ads_data):
        try:
            # Assign user (rotate through available users)
            user = users[i % len(users)]
            
            # Create the ad with all data
            ad = Ad.objects.create(
                user=user,
                
                # Step 1: Material Type
                category=ad_data["category"],
                subcategory=ad_data["subcategory"],
                specific_material=ad_data["specific_material"],
                packaging=ad_data["packaging"],
                material_frequency=ad_data["material_frequency"],
                
                # Step 2: Specifications
                additional_specifications=ad_data["additional_specifications"],
                
                # Step 3: Material Origin
                origin=ad_data["origin"],
                
                # Step 4: Contamination
                contamination=ad_data["contamination"],
                additives=ad_data["additives"],
                storage_conditions=ad_data["storage_conditions"],
                
                # Step 5: Processing Methods
                processing_methods=ad_data["processing_methods"],
                
                # Step 6: Location & Logistics
                location=ad_data["location"],
                pickup_available=ad_data["pickup_available"],
                delivery_options=ad_data["delivery_options"],
                
                # Step 7: Quantity & Pricing
                available_quantity=ad_data["available_quantity"],
                unit_of_measurement=ad_data["unit_of_measurement"],
                minimum_order_quantity=ad_data["minimum_order_quantity"],
                starting_bid_price=ad_data["starting_bid_price"],
                currency=ad_data["currency"],
                auction_duration=ad_data["auction_duration"],
                reserve_price=ad_data["reserve_price"],
                
                # Step 8: Title, Description & Image
                title=ad_data["title"],
                description=ad_data["description"],
                keywords=ad_data["keywords"],
                
                # System fields
                current_step=8,
                is_complete=True,
                is_active=True,
                auction_start_date=timezone.now() - timedelta(days=random.randint(0, 3)),
                auction_end_date=timezone.now() + timedelta(days=random.randint(3, 15))
            )
            
            created_ads.append(ad)
            print(f"  ✅ Created ad: {ad.title}")
            
        except Exception as e:
            print(f"  ❌ Error creating ad {i+1}: {str(e)}")
    
    return created_ads

def create_sample_bids_for_new_ads(ads):
    """Create sample bids for the new ads"""
    print("💰 Creating sample bids for new ads...")
    
    users = list(User.objects.all())
    created_bids = []
    
    for ad in ads:
        # Create 1-4 bids per ad
        num_bids = random.randint(1, 4)
        
        # Get potential bidders (exclude ad owner)
        potential_bidders = [u for u in users if u != ad.user]
        
        if len(potential_bidders) < num_bids:
            num_bids = len(potential_bidders)
        
        if num_bids > 0:
            bidders = random.sample(potential_bidders, num_bids)
            
            # Create bids with increasing amounts
            current_price = ad.starting_bid_price
            
            for i, bidder in enumerate(bidders):
                # Increase bid amount by 3-12%
                increase_factor = Decimal(str(1 + random.uniform(0.03, 0.12)))
                bid_price = current_price * increase_factor
                
                # Random volume (between min order and available quantity)
                min_vol = float(ad.minimum_order_quantity)
                max_vol = float(ad.available_quantity)
                bid_volume = Decimal(str(random.uniform(min_vol, min(max_vol, min_vol * 2.5))))
                
                try:
                    bid = Bid.objects.create(
                        ad=ad,
                        user=bidder,
                        bid_price_per_unit=bid_price.quantize(Decimal('0.01')),
                        volume_requested=bid_volume.quantize(Decimal('0.01')),
                        volume_type="partial",
                        status="winning" if i == len(bidders) - 1 else "outbid"
                    )
                    
                    created_bids.append(bid)
                    current_price = bid_price
                    
                    print(f"    💸 {bidder.name}: {bid.bid_price_per_unit} {ad.currency} for {bid.volume_requested} {ad.unit_of_measurement} on '{ad.title[:40]}...'")
                    
                except Exception as e:
                    print(f"    ❌ Error creating bid: {str(e)}")
    
    return created_bids

def add_additional_auction_data():
    """Main function to add 10 additional auction ads"""
    print("🚀 Adding 10 additional auction ads to Nordic Loop Platform...")
    print("=" * 70)
    
    # Create additional ads
    new_ads = create_additional_ads()
    
    if new_ads:
        # Create sample bids for new ads
        new_bids = create_sample_bids_for_new_ads(new_ads)
        
        print("\n" + "=" * 70)
        print("🎉 Additional auction data creation complete!")
        print(f"📊 Added:")
        print(f"   🏭 New Ads: {len(new_ads)}")
        print(f"   💰 New Bids: {len(new_bids)}")
        
        print(f"\n📊 Current Totals:")
        print(f"   👥 Total Users: {User.objects.count()}")
        print(f"   🏢 Total Companies: {Company.objects.count()}")
        print(f"   📍 Total Locations: {Location.objects.count()}")
        print(f"   🏭 Total Ads: {Ad.objects.count()}")
        print(f"   💰 Total Bids: {Bid.objects.count()}")
        
        print(f"\n📋 Newly Added Auctions:")
        for ad in new_ads:
            bid_count = ad.bids.count()
            highest_bid = ad.bids.order_by('-bid_price_per_unit').first()
            highest_amount = highest_bid.bid_price_per_unit if highest_bid else ad.starting_bid_price
            print(f"   🎯 {ad.title[:45]}... - {bid_count} bids - Highest: {highest_amount} {ad.currency}")
    else:
        print("❌ No ads were created. Please check the error messages above.")

if __name__ == "__main__":
    add_additional_auction_data() 