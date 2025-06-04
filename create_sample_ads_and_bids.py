#!/usr/bin/env python
"""
Sample Data Creation Script for Nordic Loop Platform
Creates realistic ads (auctions) and bids for testing and demonstration
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

def create_additional_users():
    """Create additional users for bidding"""
    print("🧑‍💼 Creating additional users...")
    
    companies_data = [
        {
            "official_name": "EcoRecycle Solutions AB",
            "vat_number": "SE987654321",
            "email": "info@ecorecycle.se",
            "primary_email": "maria@ecorecycle.se",
            "primary_first_name": "Maria",
            "primary_last_name": "Andersson",
            "sector": "recycling",
            "country": "Sweden",
            "website": "https://ecorecycle.se"
        },
        {
            "official_name": "PlastiCorp Industries",
            "vat_number": "SE456789123",
            "email": "contact@plasticorp.com",
            "primary_email": "erik@plasticorp.com",
            "primary_first_name": "Erik",
            "primary_last_name": "Lundberg",
            "sector": "manufacturing  & Production",
            "country": "Sweden",
            "website": "https://plasticorp.com"
        },
        {
            "official_name": "Green Materials Ltd",
            "vat_number": "SE789123456",
            "email": "hello@greenmaterials.eu",
            "primary_email": "anna@greenmaterials.eu",
            "primary_first_name": "Anna",
            "primary_last_name": "Pettersson",
            "sector": "packaging",
            "country": "Sweden",
            "website": "https://greenmaterials.eu"
        }
    ]
    
    created_users = []
    
    for company_data in companies_data:
        # Create company
        company, created = Company.objects.get_or_create(
            primary_email=company_data["primary_email"],
            defaults={
                "official_name": company_data["official_name"],
                "vat_number": company_data["vat_number"],
                "email": company_data["email"],
                "sector": company_data["sector"],
                "country": company_data["country"],
                "website": company_data["website"],
                "primary_first_name": company_data["primary_first_name"],
                "primary_last_name": company_data["primary_last_name"],
                "primary_position": "Manager",
                "status": "approved"
            }
        )
        
        if created:
            print(f"  ✅ Created company: {company.official_name}")
        
        # Create user
        user, created = User.objects.get_or_create(
            email=company_data["primary_email"],
            defaults={
                "username": f"{company_data['primary_first_name'].lower()}{company_data['primary_last_name'].lower()}",
                "name": f"{company_data['primary_first_name']} {company_data['primary_last_name']}",
                "company": company
            }
        )
        
        if created:
            user.set_password("testpass123")
            user.save()
            print(f"  ✅ Created user: {user.username}")
        
        created_users.append(user)
    
    return created_users

def create_sample_locations():
    """Create sample locations"""
    print("📍 Creating sample locations...")
    
    locations_data = [
        {
            "country": "Sweden",
            "state_province": "Stockholm County",
            "city": "Stockholm",
            "address_line": "Industrivägen 15",
            "postal_code": "11234",
            "latitude": 59.3293,
            "longitude": 18.0686
        },
        {
            "country": "Sweden", 
            "state_province": "Västra Götaland County",
            "city": "Gothenburg",
            "address_line": "Hamngatan 42",
            "postal_code": "41108",
            "latitude": 57.7089,
            "longitude": 11.9746
        },
        {
            "country": "Sweden",
            "state_province": "Skåne County", 
            "city": "Malmö",
            "address_line": "Österport 88",
            "postal_code": "21120",
            "latitude": 55.6059,
            "longitude": 13.0007
        },
        {
            "country": "Norway",
            "state_province": "Oslo",
            "city": "Oslo",
            "address_line": "Nydalen Park 25",
            "postal_code": "0484",
            "latitude": 59.9139,
            "longitude": 10.7522
        },
        {
            "country": "Denmark",
            "state_province": "Capital Region",
            "city": "Copenhagen",
            "address_line": "Ørestads Boulevard 73",
            "postal_code": "2300",
            "latitude": 55.6761,
            "longitude": 12.5683
        }
    ]
    
    created_locations = []
    for loc_data in locations_data:
        location, created = Location.objects.get_or_create(
            city=loc_data["city"],
            country=loc_data["country"],
            defaults=loc_data
        )
        if created:
            print(f"  ✅ Created location: {location}")
        created_locations.append(location)
    
    return created_locations

def create_sample_ads():
    """Create sample ads with complete 8-step data"""
    print("🏭 Creating sample material ads...")
    
    # Get required data
    users = list(User.objects.all())
    locations = create_sample_locations()
    
    # Get categories and subcategories
    plastics_cat = Category.objects.get(name="Plastics")
    paper_cat = Category.objects.get(name="Paper")
    metals_cat = Category.objects.get(name="Metals")
    
    pp_subcat = SubCategory.objects.get(name="PP", category=plastics_cat)
    hdpe_subcat = SubCategory.objects.get(name="HDPE", category=plastics_cat)
    pet_subcat = SubCategory.objects.get(name="PET", category=plastics_cat)
    cardboard_subcat = SubCategory.objects.get(name="Cardboard", category=paper_cat)
    aluminum_subcat = SubCategory.objects.get(name="Aluminum", category=metals_cat)
    
    sample_ads_data = [
        {
            # Step 1: Material Type
            "category": plastics_cat,
            "subcategory": pp_subcat,
            "specific_material": "High-grade PP pellets from automotive industry",
            "packaging": "octabin",
            "material_frequency": "monthly",
            
            # Step 2: Specifications
            "additional_specifications": "Melt Flow Index: 2.5, Density: 0.95 g/cm³, Food grade certified, FDA approved, Low VOC",
            
            # Step 3: Material Origin
            "origin": "post_industrial",
            
            # Step 4: Contamination
            "contamination": "clean",
            "additives": "antioxidant",
            "storage_conditions": "climate_controlled",
            
            # Step 5: Processing Methods
            "processing_methods": ["extrusion", "injection_moulding"],
            
            # Step 6: Location & Logistics
            "location": locations[0],  # Stockholm
            "pickup_available": True,
            "delivery_options": ["local_delivery", "national_shipping"],
            
            # Step 7: Quantity & Pricing
            "available_quantity": Decimal("150.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("10.00"),
            "starting_bid_price": Decimal("1250.00"),
            "currency": "EUR",
            "auction_duration": 7,
            "reserve_price": Decimal("1400.00"),
            
            # Step 8: Title, Description & Image
            "title": "Premium PP Pellets - Automotive Grade",
            "description": "High-quality polypropylene pellets sourced from automotive manufacturing. Perfect for injection molding and extrusion applications. FDA approved and food grade certified with excellent mechanical properties.",
            "keywords": "PP, polypropylene, automotive, food grade, injection molding"
        },
        {
            # HDPE Bottles
            "category": plastics_cat,
            "subcategory": hdpe_subcat,
            "specific_material": "HDPE milk bottles, cleaned and sorted",
            "packaging": "baled",
            "material_frequency": "weekly",
            
            "additional_specifications": "Density: 0.96 g/cm³, Clean white bottles, sorted by size, minimal contamination",
            
            "origin": "post_consumer",
            
            "contamination": "slightly_contaminated",
            "additives": "no_additives",
            "storage_conditions": "protected_outdoor",
            
            "processing_methods": ["blow_moulding", "extrusion"],
            
            "location": locations[1],  # Gothenburg
            "pickup_available": True,
            "delivery_options": ["pickup_only", "local_delivery"],
            
            "available_quantity": Decimal("75.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("5.00"),
            "starting_bid_price": Decimal("850.00"),
            "currency": "EUR",
            "auction_duration": 5,
            "reserve_price": Decimal("950.00"),
            
            "title": "Clean HDPE Milk Bottles - Weekly Supply",
            "description": "Consistently sourced HDPE milk bottles from dairy collection routes. Clean, sorted material perfect for recycling into new bottles or other HDPE products. Weekly availability ensures steady supply.",
            "keywords": "HDPE, milk bottles, post-consumer, recycling, blow molding"
        },
        {
            # PET Bottles
            "category": plastics_cat,
            "subcategory": pet_subcat,
            "specific_material": "Clear PET bottles, beverage grade",
            "packaging": "loose",
            "material_frequency": "bi_weekly",
            
            "additional_specifications": "Clear PET bottles, various sizes, caps removed, labels intact, beverage grade quality",
            
            "origin": "post_consumer",
            
            "contamination": "clean",
            "additives": "no_additives",
            "storage_conditions": "climate_controlled",
            
            "processing_methods": ["blow_moulding", "thermoforming"],
            
            "location": locations[2],  # Malmö
            "pickup_available": False,
            "delivery_options": ["national_shipping", "international_shipping"],
            
            "available_quantity": Decimal("200.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("15.00"),
            "starting_bid_price": Decimal("950.00"),
            "currency": "EUR",
            "auction_duration": 10,
            "reserve_price": Decimal("1100.00"),
            
            "title": "Clear PET Bottles - Beverage Grade Quality",
            "description": "Premium clear PET bottles collected from beverage industry. Excellent clarity and purity, suitable for food-grade recycling. Bi-weekly collection ensures consistent quality and supply.",
            "keywords": "PET, bottles, clear, beverage grade, food grade, recycling"
        },
        {
            # Cardboard
            "category": paper_cat,
            "subcategory": cardboard_subcat,
            "specific_material": "Corrugated cardboard boxes, industrial packaging",
            "packaging": "baled",
            "material_frequency": "weekly",
            
            "additional_specifications": "Brown corrugated cardboard, various sizes, minimal tape and staples, dry storage",
            
            "origin": "post_industrial",
            
            "contamination": "clean",
            "additives": "no_additives",
            "storage_conditions": "protected_outdoor",
            
            "processing_methods": ["calendering"],
            
            "location": locations[3],  # Oslo
            "pickup_available": True,
            "delivery_options": ["pickup_only", "local_delivery", "national_shipping"],
            
            "available_quantity": Decimal("300.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("20.00"),
            "starting_bid_price": Decimal("180.00"),
            "currency": "EUR",
            "auction_duration": 7,
            "reserve_price": Decimal("220.00"),
            
            "title": "Industrial Corrugated Cardboard - Weekly Supply",
            "description": "High-quality corrugated cardboard from industrial packaging operations. Clean, dry material perfect for paper recycling. Consistent weekly volumes available.",
            "keywords": "cardboard, corrugated, industrial, packaging, paper recycling"
        },
        {
            # Aluminum
            "category": metals_cat,
            "subcategory": aluminum_subcat,
            "specific_material": "Aluminum beverage cans, sorted and cleaned",
            "packaging": "baled",
            "material_frequency": "monthly",
            
            "additional_specifications": "Aluminum cans, various beverage brands, magnetically sorted, cleaned, compressed bales",
            
            "origin": "post_consumer",
            
            "contamination": "clean",
            "additives": "no_additives",
            "storage_conditions": "protected_outdoor",
            
            "processing_methods": ["sintering"],
            
            "location": locations[4],  # Copenhagen
            "pickup_available": True,
            "delivery_options": ["local_delivery", "national_shipping", "international_shipping"],
            
            "available_quantity": Decimal("50.00"),
            "unit_of_measurement": "tons",
            "minimum_order_quantity": Decimal("2.00"),
            "starting_bid_price": Decimal("1800.00"),
            "currency": "EUR",
            "auction_duration": 14,
            "reserve_price": Decimal("2000.00"),
            
            "title": "Sorted Aluminum Cans - Premium Quality",
            "description": "Premium quality aluminum beverage cans, magnetically sorted and cleaned. Perfect for aluminum recycling with high purity levels. Monthly collection from beverage distribution centers.",
            "keywords": "aluminum, cans, beverage, sorted, recycling, metal"
        }
    ]
    
    created_ads = []
    
    for i, ad_data in enumerate(sample_ads_data):
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
                auction_start_date=timezone.now() - timedelta(days=random.randint(1, 5)),
                auction_end_date=timezone.now() + timedelta(days=random.randint(2, 10))
            )
            
            created_ads.append(ad)
            print(f"  ✅ Created ad: {ad.title}")
            
        except Exception as e:
            print(f"  ❌ Error creating ad {i+1}: {str(e)}")
    
    return created_ads

def create_sample_bids(ads):
    """Create sample bids for the ads"""
    print("💰 Creating sample bids...")
    
    users = list(User.objects.all())
    created_bids = []
    
    for ad in ads:
        # Create 2-5 bids per ad
        num_bids = random.randint(2, 5)
        
        # Get potential bidders (exclude ad owner)
        potential_bidders = [u for u in users if u != ad.user]
        
        if len(potential_bidders) < num_bids:
            num_bids = len(potential_bidders)
        
        bidders = random.sample(potential_bidders, num_bids)
        
        # Create bids with increasing amounts
        current_price = ad.starting_bid_price
        
        for i, bidder in enumerate(bidders):
            # Increase bid amount by 5-15%
            increase_factor = Decimal(str(1 + random.uniform(0.05, 0.15)))
            bid_amount = current_price * increase_factor
            
            # Random volume (between min order and available quantity)
            min_vol = float(ad.minimum_order_quantity)
            max_vol = float(ad.available_quantity)
            bid_volume = Decimal(str(random.uniform(min_vol, min(max_vol, min_vol * 3))))
            
            try:
                bid = Bid.objects.create(
                    ad=ad,
                    user=bidder,
                    amount=bid_amount.quantize(Decimal('0.01')),
                    volume=bid_volume.quantize(Decimal('0.01')),
                    current_Highest_amount=bid_amount.quantize(Decimal('0.01')),
                    status="Highest_bid" if i == len(bidders) - 1 else "Outbid"
                )
                
                created_bids.append(bid)
                current_price = bid_amount
                
                print(f"    💸 {bidder.name}: {bid.amount} {ad.currency} for {bid.volume} {ad.unit_of_measurement} on '{ad.title[:50]}...'")
                
            except Exception as e:
                print(f"    ❌ Error creating bid: {str(e)}")
    
    return created_bids

def create_sample_data():
    """Main function to create all sample data"""
    print("🚀 Creating comprehensive sample data for Nordic Loop Platform...")
    print("=" * 70)
    
    # Create additional users
    additional_users = create_additional_users()
    
    # Create sample ads
    ads = create_sample_ads()
    
    # Create sample bids
    bids = create_sample_bids(ads)
    
    print("\n" + "=" * 70)
    print("🎉 Sample data creation complete!")
    print(f"📊 Summary:")
    print(f"   👥 Total Users: {User.objects.count()}")
    print(f"   🏢 Total Companies: {Company.objects.count()}")
    print(f"   📍 Total Locations: {Location.objects.count()}")
    print(f"   🏭 Total Ads: {Ad.objects.count()}")
    print(f"   💰 Total Bids: {Bid.objects.count()}")
    
    print(f"\n📋 Active Auctions:")
    active_ads = Ad.objects.filter(is_active=True, is_complete=True)
    for ad in active_ads:
        bid_count = ad.bids.count()
        highest_bid = ad.bids.order_by('-amount').first()
        highest_amount = highest_bid.amount if highest_bid else ad.starting_bid_price
        print(f"   🎯 {ad.title[:40]}... - {bid_count} bids - Highest: {highest_amount} {ad.currency}")
    
    print(f"\n🔗 API Testing Endpoints:")
    print(f"   📝 Login: POST http://localhost:8000/api/users/login/")
    print(f"   📋 List Materials: GET http://localhost:8000/api/ads/")
    print(f"   💰 List Bids: GET http://localhost:8000/api/bids/")
    print(f"   👤 User Materials: GET http://localhost:8000/api/ads/user/")

if __name__ == "__main__":
    create_sample_data() 