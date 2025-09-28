#!/usr/bin/env python3
"""
Script to create okarera@gmail.com user with company and sample ads
"""

import os
import sys
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from company.models import Company
from ads.models import Ad, Location
from category.models import Category, SubCategory
from django.contrib.auth.hashers import make_password

User = get_user_model()

def create_okarera_user():
    """Create okarera user with company and sample ads"""
    print("🏗️ Creating okarera@gmail.com user setup...")
    
    # 1. Create or get the user
    email = "okarera@gmail.com"
    password = "Krol@2027"
    
    try:
        user = User.objects.get(email=email)
        print(f"✅ User {email} already exists")
    except User.DoesNotExist:
        user = User.objects.create(
            email=email,
            username=email,
            first_name="Oliver",
            last_name="Karera", 
            contact_type="business",
            role="admin",
            can_place_ads=True,
            can_place_bids=True,
            is_active=True,
            is_staff=True,
            is_superuser=True,
            password=make_password(password)
        )
        print(f"✅ Created user: {email}")
    
    # 2. Create or get company for the user
    try:
        company = user.company
        if company:
            # Make sure existing company is payment ready
            company.payment_ready = True
            company.stripe_capabilities_complete = True
            company.stripe_onboarding_complete = True
            company.save()
            print(f"✅ Company already exists: {company.official_name}")
        else:
            raise AttributeError("No company found")
    except (AttributeError, Company.DoesNotExist):
        company = Company.objects.create(
            official_name="Karera Industries AB",
            vat_number="SE556789012301",
            email=user.email,
            sector="recycling",
            country="Sweden",
            website="https://karera-industries.se",
            status="approved"
        )
        
        # Set company as payment ready for testing
        company.payment_ready = True
        company.stripe_capabilities_complete = True
        company.stripe_onboarding_complete = True
        company.save()
        
        # Link user to company
        user.company = company
        user.save()
        print(f"✅ Created company: {company.official_name}")
    
    # 3. Create locations for ads
    locations = []
    
    # Stockholm location
    stockholm_location, created = Location.objects.get_or_create(
        country="Sweden",
        city="Stockholm",
        defaults={
            'state_province': 'Stockholm County',
            'address_line': 'Industrigatan 15',
            'postal_code': '11234'
        }
    )
    locations.append(stockholm_location)
    
    # Gothenburg location  
    gothenburg_location, created = Location.objects.get_or_create(
        country="Sweden", 
        city="Gothenburg",
        defaults={
            'state_province': 'Västra Götaland County',
            'address_line': 'Hamngatan 22',
            'postal_code': '40123'
        }
    )
    locations.append(gothenburg_location)
    
    print(f"✅ Created/found {len(locations)} locations")
    
    # 4. Get categories for ads
    try:
        metal_category = Category.objects.get(name__icontains='metal')
    except Category.DoesNotExist:
        metal_category = Category.objects.filter(name='Metals').first()
        if not metal_category:
            metal_category = Category.objects.create(name="Metals")
    
    try:
        plastic_category = Category.objects.get(name__icontains='plastic')
    except Category.DoesNotExist:
        print("❌ Plastic category not found. Creating one...")
        plastic_category = Category.objects.create(name="Plastics")
    
    # Get subcategories
    plastic_subcats = list(SubCategory.objects.filter(category=plastic_category)[:2])
    metal_subcats = list(SubCategory.objects.filter(category=metal_category)[:2])
    
    print(f"✅ Found categories: {plastic_category.name}, {metal_category.name}")
    
    # 5. Create sample ads
    ads_created = 0
    
    # Plastic ads
    plastic_ads = [
        {
            'title': 'High-Quality HDPE Bottles for Recycling',
            'description': 'Clean HDPE milk and juice bottles from our collection network. Perfect for recycling into new containers or pellets. Material is sorted, washed, and ready for processing. Consistent monthly supply available.',
            'specific_material': 'HDPE bottles from dairy and juice industry',
            'available_quantity': Decimal('15.5'),
            'starting_bid_price': Decimal('2.80'),
            'category': plastic_category,
            'subcategory': plastic_subcats[0] if plastic_subcats else None,
        },
        {
            'title': 'PET Bottle Flakes - Food Grade',
            'description': 'Premium PET bottle flakes from beverage containers. Hot-washed and sorted to food-grade standards. Ideal for bottle-to-bottle recycling or textile fiber production. Regular supply from our Nordic operations.',
            'specific_material': 'Clear PET bottle flakes, food-grade quality',
            'available_quantity': Decimal('25.0'),
            'starting_bid_price': Decimal('3.20'),
            'category': plastic_category,
            'subcategory': plastic_subcats[1] if len(plastic_subcats) > 1 else plastic_subcats[0] if plastic_subcats else None,
        },
        {
            'title': 'Mixed Plastic Waste - Industrial Grade',
            'description': 'Sorted mixed plastic waste from industrial sources. Contains PP, PE, and PS materials suitable for downcycling applications. Clean and contaminant-free. Great for plastic lumber or composite applications.',
            'specific_material': 'Mixed PP/PE/PS from industrial packaging',
            'available_quantity': Decimal('50.0'),
            'starting_bid_price': Decimal('1.50'),
            'category': plastic_category,
            'subcategory': plastic_subcats[0] if plastic_subcats else None,
        }
    ]
    
    # Metal ads
    metal_ads = [
        {
            'title': 'Aluminum Cans - Beverage Industry',
            'description': 'Clean aluminum beverage cans from our collection network across Sweden. Sorted and compacted for efficient transport. Perfect for aluminum smelting and new can production. Consistent supply guaranteed.',
            'specific_material': 'Aluminum beverage cans, food-grade',
            'available_quantity': Decimal('8.5'),
            'starting_bid_price': Decimal('12.50'),
            'category': metal_category,
            'subcategory': metal_subcats[0] if metal_subcats else None,
        },
        {
            'title': 'Copper Wire Scrap - Electronics',
            'description': 'High-purity copper wire scrap from electronic waste processing. Stripped and sorted by gauge. Excellent for copper refineries and wire manufacturing. Premium grade with minimal contamination.',
            'specific_material': 'Copper wire from electronics, 99% purity',
            'available_quantity': Decimal('2.3'),
            'starting_bid_price': Decimal('45.00'),
            'category': metal_category,
            'subcategory': metal_subcats[1] if len(metal_subcats) > 1 else metal_subcats[0] if metal_subcats else None,
        }
    ]
    
    all_ads = plastic_ads + metal_ads
    
    for i, ad_data in enumerate(all_ads):
        # Check if ad already exists
        existing = Ad.objects.filter(user=user, title=ad_data['title']).first()
        if existing:
            print(f"  ⚠️ Ad already exists: {ad_data['title']}")
            continue
            
        # Create the ad
        ad = Ad.objects.create(
            user=user,
            title=ad_data['title'],
            description=ad_data['description'],
            specific_material=ad_data['specific_material'],
            category=ad_data['category'],
            subcategory=ad_data['subcategory'],
            packaging='baled' if 'Flakes' in ad_data['title'] else 'loose',
            material_frequency='monthly',
            origin='post_industrial' if 'Industrial' in ad_data['title'] else 'post_consumer',
            contamination='clean',
            additives='no_additives',
            storage_conditions='protected_outdoor',
            processing_methods=['extrusion', 'blow_moulding'] if ad_data['category'] == plastic_category else ['sintering'],
            location=locations[i % len(locations)],
            delivery_options=['pickup_only', 'local_delivery', 'national_shipping'],
            available_quantity=ad_data['available_quantity'],
            unit_of_measurement='tons',
            minimum_order_quantity=Decimal('1.0'),
            starting_bid_price=ad_data['starting_bid_price'],
            currency='EUR',
            auction_duration=7,
            keywords=f"recycling, {ad_data['category'].name.lower()}, sustainable, nordic",
            status='active',
            auction_start_date=timezone.now(),
            auction_end_date=timezone.now() + timedelta(days=7),
            current_step=8,
            is_complete=True,
            step_1_complete=True,
            step_2_complete=True,
            step_3_complete=True,
            step_4_complete=True,
            step_5_complete=True,
            step_6_complete=True,
            step_7_complete=True,
            step_8_complete=True
        )
        
        ads_created += 1
        print(f"  ✅ Created ad: {ad.title}")
    
    print(f"\n🎉 Setup Complete!")
    print(f"👤 User: {user.email}")
    print(f"🏢 Company: {company.official_name}")
    print(f"📦 Ads created: {ads_created}")
    print(f"📍 Locations: {len(locations)}")
    print(f"\n🔑 Login credentials:")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"\n🌐 User can now login and access their dashboard with {Ad.objects.filter(user=user).count()} total ads")

if __name__ == "__main__":
    create_okarera_user()