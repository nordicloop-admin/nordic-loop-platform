#!/usr/bin/env python
"""
Realistic Ads and Bids Creation Script for Nordic Loop Platform

This script creates 25 realistic ads with proper specifications and 15 bids
to demonstrate the complete marketplace functionality.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from ads.models import Ad, Location
from bids.models import Bid
from category.models import Category, SubCategory, CategorySpecification
from company.models import Company

User = get_user_model()


def create_locations():
    """Create diverse locations across Europe"""
    locations_data = [
        # Nordic countries
        {"country": "Sweden", "state_province": "Stockholm County", "city": "Stockholm", "address_line": "Kungsgatan 15", "postal_code": "111 43", "latitude": 59.3293, "longitude": 18.0686},
        {"country": "Sweden", "state_province": "Västra Götaland", "city": "Gothenburg", "address_line": "Kungsportsavenyn 22", "postal_code": "411 36", "latitude": 57.7089, "longitude": 11.9746},
        {"country": "Norway", "state_province": "Oslo", "city": "Oslo", "address_line": "Karl Johans gate 5", "postal_code": "0154", "latitude": 59.9139, "longitude": 10.7522},
        {"country": "Denmark", "state_province": "Capital Region", "city": "Copenhagen", "address_line": "Strøget 12", "postal_code": "1160", "latitude": 55.6761, "longitude": 12.5683},
        {"country": "Finland", "state_province": "Uusimaa", "city": "Helsinki", "address_line": "Mannerheimintie 18", "postal_code": "00100", "latitude": 60.1695, "longitude": 24.9354},
        
        # Central Europe
        {"country": "Germany", "state_province": "North Rhine-Westphalia", "city": "Düsseldorf", "address_line": "Königsallee 45", "postal_code": "40212", "latitude": 51.2277, "longitude": 6.7735},
        {"country": "Netherlands", "state_province": "North Holland", "city": "Amsterdam", "address_line": "Damrak 70", "postal_code": "1012 LM", "latitude": 52.3676, "longitude": 4.9041},
        {"country": "Belgium", "state_province": "Brussels", "city": "Brussels", "address_line": "Rue de la Loi 155", "postal_code": "1040", "latitude": 50.8503, "longitude": 4.3517},
        
        # Eastern Europe
        {"country": "Poland", "state_province": "Masovian Voivodeship", "city": "Warsaw", "address_line": "Aleje Jerozolimskie 65", "postal_code": "00-697", "latitude": 52.2297, "longitude": 21.0122},
        {"country": "Czech Republic", "state_province": "Prague", "city": "Prague", "address_line": "Wenceslas Square 15", "postal_code": "110 00", "latitude": 50.0755, "longitude": 14.4378},
        
        # UK & Ireland
        {"country": "United Kingdom", "state_province": "England", "city": "London", "address_line": "Oxford Street 150", "postal_code": "W1D 1NB", "latitude": 51.5074, "longitude": -0.1278},
        {"country": "Ireland", "state_province": "Dublin", "city": "Dublin", "address_line": "O'Connell Street 42", "postal_code": "D01 F5P2", "latitude": 53.3498, "longitude": -6.2603},
    ]
    
    locations = []
    for loc_data in locations_data:
        location, created = Location.objects.get_or_create(
            country=loc_data["country"],
            city=loc_data["city"],
            address_line=loc_data["address_line"],
            defaults=loc_data
        )
        locations.append(location)
        if created:
            print(f"  ✓ Created location: {location.city}, {location.country}")
    
    return locations


def create_realistic_specifications():
    """Create realistic category specifications"""
    specs_data = []
    
    # Get categories
    plastics = Category.objects.get(name="Plastics")
    paper = Category.objects.get(name="Paper")
    metals = Category.objects.get(name="Metals")
    glass = Category.objects.get(name="Glass")
    
    # Clear existing specifications to avoid duplicates
    CategorySpecification.objects.all().delete()
    print("  ✓ Cleared existing specifications")
    
    # Plastics specifications (create multiple unique ones)
    plastic_specs = [
        {"Category": plastics, "color": "Natural/Clear", "material_grade": "virgin_grade", "material_form": "pellets_granules", "additional_specifications": "Melt Flow Index: 12 g/10min, Density: 0.905 g/cm³, Food grade certified"},
        {"Category": plastics, "color": "White", "material_grade": "industrial_grade", "material_form": "flakes", "additional_specifications": "Clean HDPE bottles, labels removed, 98% purity"},
        {"Category": plastics, "color": "Mixed Colors", "material_grade": "recycled_grade", "material_form": "regrind", "additional_specifications": "Mixed PP automotive parts, sorted by type, metal free"},
        {"Category": plastics, "color": "Black", "material_grade": "automotive_grade", "material_form": "sheets", "additional_specifications": "UV stabilized, impact modified, automotive interior grade"},
        {"Category": plastics, "color": "Blue", "material_grade": "medical_grade", "material_form": "pellets_granules", "additional_specifications": "USP Class VI certified, gamma sterilizable, biocompatible"},
        {"Category": plastics, "color": "Green", "material_grade": "food_grade", "material_form": "film", "additional_specifications": "LDPE agricultural film, UV stabilized, soil contamination"},
        {"Category": plastics, "color": "Gray", "material_grade": "electrical_grade", "material_form": "parts_components", "additional_specifications": "ABS electronics housing, flame retardant grade"},
        {"Category": plastics, "color": "Natural/Clear", "material_grade": "food_grade", "material_form": "parts_components", "additional_specifications": "PET bottles, food contact approved, clear"},
        {"Category": plastics, "color": "Yellow", "material_grade": "medical_grade", "material_form": "parts_components", "additional_specifications": "PEEK medical components, biocompatible"},
    ]
    
    # Paper specifications
    paper_specs = [
        {"Category": paper, "color": "White", "material_grade": "industrial_grade", "material_form": "sheets", "additional_specifications": "Office paper, 80gsm, minimal ink contamination"},
        {"Category": paper, "color": "Brown", "material_grade": "recycled_grade", "material_form": "fiber", "additional_specifications": "Corrugated cardboard, moisture content <8%, food grade"},
        {"Category": paper, "color": "Mixed Colors", "material_grade": "recycled_grade", "material_form": "sheets", "additional_specifications": "Mixed newspaper and magazines, standard newsprint"},
    ]
    
    # Metal specifications  
    metal_specs = [
        {"Category": metals, "material_grade": "industrial_grade", "material_form": "sheets", "additional_specifications": "6061-T6 aluminum, 2mm thickness, aerospace grade"},
        {"Category": metals, "material_grade": "recycled_grade", "material_form": "parts_components", "additional_specifications": "Mixed copper wire, 99.9% purity, insulation removed"},
        {"Category": metals, "material_grade": "medical_grade", "material_form": "sheets", "additional_specifications": "316L stainless steel, biocompatible, medical grade"},
        {"Category": metals, "material_grade": "industrial_grade", "material_form": "parts_components", "additional_specifications": "Mixed structural steel, construction grade"},
    ]
    
    # Glass specifications
    glass_specs = [
        {"Category": glass, "color": "Natural/Clear", "material_grade": "food_grade", "material_form": "parts_components", "additional_specifications": "Clear glass bottles, various sizes, food contact approved"},
        {"Category": glass, "color": "Mixed Colors", "material_grade": "industrial_grade", "material_form": "parts_components", "additional_specifications": "Mixed colored glass, industrial applications"},
    ]
    
    all_specs = plastic_specs + paper_specs + metal_specs + glass_specs
    
    for spec_data in all_specs:
        spec = CategorySpecification.objects.create(**spec_data)
        specs_data.append(spec)
        print(f"  ✓ Created specification: {spec}")
    
    return specs_data


def create_realistic_ads():
    """Create 25 realistic ads with proper specifications"""
    
    print("\n🏭 Creating realistic ads...")
    
    # Get users and other data
    users = list(User.objects.filter(is_superuser=False, company__isnull=False))
    locations = create_locations()
    specifications = create_realistic_specifications()
    
    # Define realistic ad data
    ads_data = [
        # Plastics Ads
        {
            "title": "High-Quality HDPE Bottles - Food Grade",
            "category": "Plastics", "subcategory": "HDPE",
            "specific_material": "HDPE milk bottles, cleaned and sorted",
            "packaging": "big_bag", "material_frequency": "weekly",
            "specification_type": "virgin_grade_pellets",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["blow_moulding", "injection_moulding"],
            "available_quantity": Decimal("120.00"), "unit": "tons", "min_order": Decimal("10.00"),
            "starting_price": Decimal("850.00"), "currency": "EUR", "duration": 7, "reserve": Decimal("950.00"),
            "description": "Premium quality HDPE milk bottles sourced from major dairy processors. All bottles are cleaned, sorted, and free from contamination. Perfect for food-grade recycling applications with consistent weekly supply.",
            "keywords": "HDPE, food grade, milk bottles, clean, recycling"
        },
        {
            "title": "Virgin PP Pellets - Automotive Grade",
            "category": "Plastics", "subcategory": "PP",
            "specific_material": "Virgin polypropylene pellets for automotive applications",
            "packaging": "octabin", "material_frequency": "monthly",
            "specification_type": "automotive_grade_pellets",
            "origin": "post_industrial", "contamination": "clean", "additives": "uv_stabilizer", "storage_conditions": "climate_controlled",
            "processing_methods": ["injection_moulding", "extrusion"],
            "available_quantity": Decimal("50.00"), "unit": "tons", "min_order": Decimal("5.00"),
            "starting_price": Decimal("1200.00"), "currency": "EUR", "duration": 0, "custom_duration": 21, "reserve": Decimal("1350.00"),
            "description": "High-performance virgin PP pellets specifically designed for automotive interior applications. UV stabilized and impact modified for superior durability and appearance.",
            "keywords": "PP, virgin, automotive, UV stabilized, interior"
        },
        {
            "title": "Mixed Plastic Flakes - Industrial Grade",
            "category": "Plastics", "subcategory": "Mixed hard plastics",
            "specific_material": "Mixed hard plastic flakes from household collection",
            "packaging": "loose", "material_frequency": "bi_weekly",
            "specification_type": "recycled_grade_flakes",
            "origin": "post_consumer", "contamination": "slightly_contaminated", "additives": "mixed", "storage_conditions": "protected_outdoor",
            "processing_methods": ["extrusion", "calendering"],
            "available_quantity": Decimal("200.00"), "unit": "tons", "min_order": Decimal("20.00"),
            "starting_price": Decimal("420.00"), "currency": "EUR", "duration": 10, "reserve": Decimal("500.00"),
            "description": "Large volume mixed plastic flakes suitable for industrial applications. Material includes HDPE, PP, and PET from household recycling programs. Ideal for non-food applications.",
            "keywords": "mixed plastics, flakes, industrial, household, recycling"
        },
        {
            "title": "Clear PET Bottles - Beverage Grade",
            "category": "Plastics", "subcategory": "PET",
            "specific_material": "Clear PET bottles from beverage industry",
            "packaging": "baled", "material_frequency": "weekly",
            "specification_type": "food_grade_parts",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["blow_moulding", "extrusion"],
            "available_quantity": Decimal("80.00"), "unit": "tons", "min_order": Decimal("8.00"),
            "starting_price": Decimal("720.00"), "currency": "EUR", "duration": 7, "reserve": Decimal("820.00"),
            "description": "High-quality clear PET bottles from major beverage companies. Labels removed, caps separated. Perfect for bottle-to-bottle recycling with food contact approval.",
            "keywords": "PET, bottles, beverage, clear, food contact"
        },
        {
            "title": "Medical Grade PEEK Components",
            "category": "Plastics", "subcategory": "Other plastics",
            "specific_material": "PEEK medical device components",
            "packaging": "container", "material_frequency": "quarterly",
            "specification_type": "medical_grade_parts",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["injection_moulding", "sintering"],
            "available_quantity": Decimal("2.50"), "unit": "tons", "min_order": Decimal("0.50"),
            "starting_price": Decimal("15000.00"), "currency": "EUR", "duration": 0, "custom_duration": 45, "reserve": Decimal("18000.00"),
            "description": "Premium medical grade PEEK components from medical device manufacturing. USP Class VI certified, biocompatible, and suitable for high-temperature sterilization.",
            "keywords": "PEEK, medical grade, biocompatible, sterilizable, premium"
        },
        {
            "title": "LDPE Film Rolls - Agricultural Waste",
            "category": "Plastics", "subcategory": "LDPE",
            "specific_material": "LDPE agricultural film and greenhouse covers",
            "packaging": "roles", "material_frequency": "yearly",
            "specification_type": "industrial_grade_film",
            "origin": "post_consumer", "contamination": "slightly_contaminated", "additives": "uv_stabilizer", "storage_conditions": "unprotected_outdoor",
            "processing_methods": ["extrusion", "blow_moulding"],
            "available_quantity": Decimal("300.00"), "unit": "tons", "min_order": Decimal("30.00"),
            "starting_price": Decimal("380.00"), "currency": "EUR", "duration": 21, "reserve": Decimal("450.00"),
            "description": "Large volume LDPE agricultural film from greenhouse operations and crop protection. Material includes UV-stabilized films with some soil contamination requiring cleaning.",
            "keywords": "LDPE, agricultural, film, greenhouse, UV stabilized"
        },
        {
            "title": "ABS Electronics Housing Waste",
            "category": "Plastics", "subcategory": "ABS",
            "specific_material": "ABS electronic device housings and cases",
            "packaging": "container", "material_frequency": "monthly",
            "specification_type": "electrical_grade_parts",
            "origin": "post_consumer", "contamination": "slightly_contaminated", "additives": "flame_retardants", "storage_conditions": "protected_outdoor",
            "processing_methods": ["injection_moulding", "extrusion"],
            "available_quantity": Decimal("15.00"), "unit": "tons", "min_order": Decimal("2.00"),
            "starting_price": Decimal("950.00"), "currency": "EUR", "duration": 14, "reserve": Decimal("1100.00"),
            "description": "ABS electronic housings from WEEE recycling. Flame retardant grade material suitable for electrical applications. Some metal inserts may be present.",
            "keywords": "ABS, electronics, flame retardant, WEEE, electrical"
        },
        
        # Paper Ads
        {
            "title": "High-Quality Office Paper Waste",
            "category": "Paper", "subcategory": "White paper",
            "specific_material": "Mixed office paper from corporate buildings",
            "packaging": "baled", "material_frequency": "weekly",
            "specification_type": "office_paper",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("150.00"), "unit": "tons", "min_order": Decimal("15.00"),
            "starting_price": Decimal("180.00"), "currency": "EUR", "duration": 7, "reserve": Decimal("220.00"),
            "description": "Premium office paper waste from major corporate buildings. Minimal ink contamination, sorted white paper only. Ideal for high-quality paper recycling.",
            "keywords": "office paper, corporate, clean, white paper, recycling"
        },
        {
            "title": "Corrugated Cardboard - Food Grade",
            "category": "Paper", "subcategory": "Cardboard",
            "specific_material": "Food-grade corrugated cardboard boxes",
            "packaging": "baled", "material_frequency": "bi_weekly",
            "specification_type": "food_grade_cardboard",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("250.00"), "unit": "tons", "min_order": Decimal("25.00"),
            "starting_price": Decimal("165.00"), "currency": "EUR", "duration": 10, "reserve": Decimal("200.00"),
            "description": "Clean corrugated cardboard from food distribution centers. Food contact approved, minimal grease contamination. Perfect for new packaging applications.",
            "keywords": "cardboard, corrugated, food grade, clean, packaging"
        },
        {
            "title": "Mixed Newspaper and Magazines",
            "category": "Paper", "subcategory": "Newspaper",
            "specific_material": "Mixed newspapers, magazines, and printed materials",
            "packaging": "baled", "material_frequency": "weekly",
            "specification_type": "newsprint_mixed",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("180.00"), "unit": "tons", "min_order": Decimal("20.00"),
            "starting_price": Decimal("140.00"), "currency": "EUR", "duration": 7, "reserve": Decimal("170.00"),
            "description": "High-volume mixed newspaper and magazine collection from distribution centers. Standard newsprint with color inserts included.",
            "keywords": "newspaper, magazines, newsprint, distribution, printing"
        },
        
        # Metals Ads
        {
            "title": "Aerospace Grade Aluminum Sheets",
            "category": "Metals", "subcategory": "Aluminium",
            "specific_material": "6061-T6 aluminum sheets from aerospace manufacturing",
            "packaging": "container", "material_frequency": "quarterly",
            "specification_type": "aerospace_aluminum",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("25.00"), "unit": "tons", "min_order": Decimal("2.00"),
            "starting_price": Decimal("2800.00"), "currency": "EUR", "duration": 21, "reserve": Decimal("3200.00"),
            "description": "Premium aerospace grade aluminum sheets with full material certificates. 6061-T6 specification with superior strength and corrosion resistance.",
            "keywords": "aluminum, aerospace, 6061-T6, certified, premium"
        },
        {
            "title": "Copper Wire - Electrical Grade",
            "category": "Metals", "subcategory": "Copper",
            "specific_material": "Stripped copper wire from electrical installations",
            "packaging": "container", "material_frequency": "monthly",
            "specification_type": "electrical_copper",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("12.00"), "unit": "tons", "min_order": Decimal("1.00"),
            "starting_price": Decimal("7800.00"), "currency": "EUR", "duration": 7, "reserve": Decimal("8500.00"),
            "description": "High-purity copper wire from electrical contractors. All insulation removed, 99.9% purity copper suitable for electrical applications.",
            "keywords": "copper, electrical, wire, high purity, contractors"
        },
        {
            "title": "Stainless Steel Scrap - Medical Grade",
            "category": "Metals", "subcategory": "Stainless steel",
            "specific_material": "316L stainless steel medical equipment scrap",
            "packaging": "container", "material_frequency": "quarterly",
            "specification_type": "medical_stainless",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("8.00"), "unit": "tons", "min_order": Decimal("1.00"),
            "starting_price": Decimal("3500.00"), "currency": "EUR", "duration": 14, "reserve": Decimal("4000.00"),
            "description": "Premium 316L stainless steel from medical equipment manufacturing. Biocompatible grade with full traceability and material certificates.",
            "keywords": "stainless steel, 316L, medical, biocompatible, certified"
        },
        {
            "title": "Mixed Iron and Steel Construction Waste",
            "category": "Metals", "subcategory": "Iron and steel",
            "specific_material": "Mixed structural steel from demolition projects",
            "packaging": "loose", "material_frequency": "monthly",
            "specification_type": "construction_steel",
            "origin": "post_consumer", "contamination": "slightly_contaminated", "additives": "no_additives", "storage_conditions": "unprotected_outdoor",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("500.00"), "unit": "tons", "min_order": Decimal("50.00"),
            "starting_price": Decimal("320.00"), "currency": "EUR", "duration": 14, "reserve": Decimal("380.00"),
            "description": "Large volume structural steel from building demolition. Mixed grades including I-beams, rebar, and sheet steel. Some rust and paint contamination present.",
            "keywords": "steel, construction, demolition, structural, mixed grades"
        },
        
        # Glass Ads
        {
            "title": "Clear Glass Bottles - Premium Quality",
            "category": "Glass", "subcategory": "Clear glass",
            "specific_material": "Clear glass bottles from beverage industry",
            "packaging": "container", "material_frequency": "weekly",
            "specification_type": "beverage_glass",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("100.00"), "unit": "tons", "min_order": Decimal("10.00"),
            "starting_price": Decimal("95.00"), "currency": "EUR", "duration": 7, "reserve": Decimal("120.00"),
            "description": "Premium clear glass bottles from major beverage producers. Labels and caps removed, sorted by color. Perfect for bottle-to-bottle recycling.",
            "keywords": "glass, bottles, clear, beverage, recycling"
        },
        {
            "title": "Mixed Color Glass - Industrial Applications",
            "category": "Glass", "subcategory": "Coloured glass",
            "specific_material": "Mixed colored glass from various sources",
            "packaging": "container", "material_frequency": "bi_weekly",
            "specification_type": "mixed_color_glass",
            "origin": "post_consumer", "contamination": "slightly_contaminated", "additives": "no_additives", "storage_conditions": "unprotected_outdoor",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("80.00"), "unit": "tons", "min_order": Decimal("8.00"),
            "starting_price": Decimal("65.00"), "currency": "EUR", "duration": 10, "reserve": Decimal("85.00"),
            "description": "Mixed colored glass including green, brown, and blue bottles. Suitable for industrial applications and non-food container manufacturing.",
            "keywords": "glass, mixed colors, industrial, non-food, containers"
        },
        
        # Textile Ads
        {
            "title": "Cotton Textile Waste - Fashion Industry",
            "category": "Textiles", "subcategory": "Cotton",
            "specific_material": "100% cotton fabric waste from garment manufacturing",
            "packaging": "baled", "material_frequency": "monthly",
            "specification_type": "cotton_waste",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("30.00"), "unit": "tons", "min_order": Decimal("3.00"),
            "starting_price": Decimal("450.00"), "currency": "EUR", "duration": 14, "reserve": Decimal("550.00"),
            "description": "High-quality cotton textile waste from fashion manufacturers. Various colors and weights, suitable for recycling into new textiles or industrial applications.",
            "keywords": "cotton, textile, fashion, manufacturing, clean"
        },
        {
            "title": "Mixed Polyester Fabrics",
            "category": "Textiles", "subcategory": "Polyester",
            "specific_material": "Mixed polyester textiles from household collection",
            "packaging": "baled", "material_frequency": "monthly",
            "specification_type": "polyester_mixed",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("40.00"), "unit": "tons", "min_order": Decimal("4.00"),
            "starting_price": Decimal("320.00"), "currency": "EUR", "duration": 14, "reserve": Decimal("400.00"),
            "description": "Mixed polyester fabrics from textile recycling programs. Various weights and colors, sorted and cleaned. Suitable for fiber recycling.",
            "keywords": "polyester, textiles, household, recycling, fibers"
        },
        
        # Building Materials
        {
            "title": "Concrete Recyclate - Road Construction",
            "category": "Building material", "subcategory": "Concrete recyclate",
            "specific_material": "Crushed concrete from highway demolition",
            "packaging": "loose", "material_frequency": "quarterly",
            "specification_type": "concrete_aggregate",
            "origin": "post_consumer", "contamination": "slightly_contaminated", "additives": "no_additives", "storage_conditions": "unprotected_outdoor",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("2000.00"), "unit": "tons", "min_order": Decimal("200.00"),
            "starting_price": Decimal("15.00"), "currency": "EUR", "duration": 30, "reserve": Decimal("25.00"),
            "description": "High-volume concrete recyclate from highway reconstruction projects. Suitable for road base and construction aggregate applications.",
            "keywords": "concrete, recyclate, highway, construction, aggregate"
        },
        {
            "title": "Recycled Bricks - Historical Buildings",
            "category": "Building material", "subcategory": "Recycled bricks",
            "specific_material": "Reclaimed bricks from historical building renovation",
            "packaging": "loose", "material_frequency": "yearly",
            "specification_type": "heritage_bricks",
            "origin": "post_consumer", "contamination": "slightly_contaminated", "additives": "no_additives", "storage_conditions": "unprotected_outdoor",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("150.00"), "unit": "tons", "min_order": Decimal("15.00"),
            "starting_price": Decimal("85.00"), "currency": "EUR", "duration": 21, "reserve": Decimal("120.00"),
            "description": "Premium reclaimed bricks from 19th century buildings. Excellent quality with character, perfect for restoration projects and architectural features.",
            "keywords": "bricks, reclaimed, historical, heritage, restoration"
        },
        
        # E-waste
        {
            "title": "Electronic Circuit Boards - Precious Metals",
            "category": "E-waste", "subcategory": "Small devices (max 50 cm)",
            "specific_material": "Mixed electronic circuit boards from IT equipment",
            "packaging": "container", "material_frequency": "monthly",
            "specification_type": "electronics_pcb",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("5.00"), "unit": "tons", "min_order": Decimal("0.50"),
            "starting_price": Decimal("8500.00"), "currency": "EUR", "duration": 14, "reserve": Decimal("9500.00"),
            "description": "High-value electronic circuit boards from IT equipment recycling. Rich in precious metals including gold, silver, and palladium. Certified WEEE processing.",
            "keywords": "electronics, PCB, precious metals, WEEE, IT equipment"
        },
        
        # Chemical Substances
        {
            "title": "Used Mineral Oil - Automotive Industry",
            "category": "Chemical substances", "subcategory": "Mineral oils",
            "specific_material": "Used automotive engine oil and hydraulic fluids",
            "packaging": "container", "material_frequency": "monthly",
            "specification_type": "used_oil",
            "origin": "post_consumer", "contamination": "slightly_contaminated", "additives": "antioxidant", "storage_conditions": "climate_controlled",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("80.00"), "unit": "tons", "min_order": Decimal("8.00"),
            "starting_price": Decimal("180.00"), "currency": "EUR", "duration": 14, "reserve": Decimal("220.00"),
            "description": "Used automotive oils from service centers and workshops. Suitable for re-refining into base oil or energy recovery. Hazardous waste certified handling.",
            "keywords": "mineral oil, automotive, used oil, re-refining, hazardous"
        },
        
        # Additional ads with new unit types
        {
            "title": "Industrial Chemical Containers - Bulk Sale",
            "category": "Chemical substances", "subcategory": "Mineral oils",
            "specific_material": "Empty chemical containers for cleaning and reuse",
            "packaging": "container", "material_frequency": "monthly",
            "specification_type": "used_oil",
            "origin": "post_industrial", "contamination": "slightly_contaminated", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("1500.00"), "unit": "pieces", "min_order": Decimal("100.00"),
            "starting_price": Decimal("12.50"), "currency": "EUR", "duration": 0, "custom_duration": 12, "reserve": Decimal("15.00"),
            "description": "Large quantity of industrial chemical containers ready for cleaning and reuse. Various sizes from 5L to 200L capacity.",
            "keywords": "containers, chemical, industrial, reuse, bulk"
        },
        {
            "title": "Bulk Plastic Granules - Mixed Colors",
            "category": "Plastics", "subcategory": "Mixed hard plastics",
            "specific_material": "Mixed plastic granules from bottle recycling",
            "packaging": "big_bag", "material_frequency": "weekly",
            "specification_type": "recycled_grade_flakes",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["extrusion", "injection_moulding"],
            "available_quantity": Decimal("50000.00"), "unit": "liters", "min_order": Decimal("5000.00"),
            "starting_price": Decimal("0.85"), "currency": "EUR", "duration": 7, "reserve": Decimal("1.20"),
            "description": "High-volume plastic granules measured by volumetric capacity. Consistent quality from automated sorting facility.",
            "keywords": "plastic, granules, volume, recycling, automated"
        },
        {
            "title": "Premium Glass Bottle Units",
            "category": "Glass", "subcategory": "Clear glass",
            "specific_material": "Premium wine and spirits bottles",
            "packaging": "container", "material_frequency": "monthly",
            "specification_type": "beverage_glass",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("25000.00"), "unit": "units", "min_order": Decimal("1000.00"),
            "starting_price": Decimal("0.45"), "currency": "EUR", "duration": 14, "reserve": Decimal("0.65"),
            "description": "Premium quality glass bottles from luxury beverage industry. Sold by individual unit count for specialized applications.",
            "keywords": "glass, bottles, premium, luxury, units"
        },
        
        # Additional 20 ads for expanded marketplace
        {
            "title": "Pharmaceutical Grade PVC Pellets",
            "category": "Plastics", "subcategory": "PVC",
            "specific_material": "Medical grade PVC pellets for pharmaceutical packaging",
            "packaging": "octabin", "material_frequency": "monthly",
            "specification_type": "medical_grade_pellets",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["injection_moulding", "extrusion"],
            "available_quantity": Decimal("15.00"), "unit": "tons", "min_order": Decimal("1.00"),
            "starting_price": Decimal("2200.00"), "currency": "EUR", "duration": 0, "custom_duration": 18, "reserve": Decimal("2500.00"),
            "description": "Ultra-high purity PVC pellets for pharmaceutical applications. Full material traceability and regulatory compliance documentation included.",
            "keywords": "PVC, pharmaceutical, medical grade, regulated, traceability"
        },
        {
            "title": "Titanium Aerospace Scrap Components",
            "category": "Metals", "subcategory": "Other metals",
            "specific_material": "Grade 5 titanium components from aerospace manufacturing",
            "packaging": "container", "material_frequency": "quarterly",
            "specification_type": "aerospace_titanium",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("850.00"), "unit": "pieces", "min_order": Decimal("50.00"),
            "starting_price": Decimal("125.00"), "currency": "EUR", "duration": 0, "custom_duration": 35, "reserve": Decimal("150.00"),
            "description": "High-value titanium components from aerospace industry. Grade 5 Ti-6Al-4V alloy with full material certificates and chain of custody.",
            "keywords": "titanium, aerospace, grade 5, certified, high value"
        },
        {
            "title": "Organic Cotton Textile Bales - GOTS Certified",
            "category": "Textiles", "subcategory": "Cotton",
            "specific_material": "GOTS certified organic cotton textile waste",
            "packaging": "baled", "material_frequency": "bi_weekly",
            "specification_type": "organic_cotton",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("125.00"), "unit": "bales", "min_order": Decimal("10.00"),
            "starting_price": Decimal("85.00"), "currency": "EUR", "duration": 14, "reserve": Decimal("110.00"),
            "description": "Premium organic cotton textile waste with GOTS certification. Perfect for sustainable fashion brands and eco-friendly textile recycling.",
            "keywords": "organic cotton, GOTS, certified, sustainable, fashion"
        },
        {
            "title": "Laboratory Glassware Collection",
            "category": "Glass", "subcategory": "Other glass",
            "specific_material": "Laboratory borosilicate glassware from research facilities",
            "packaging": "container", "material_frequency": "monthly",
            "specification_type": "laboratory_glass",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("2500.00"), "unit": "pieces", "min_order": Decimal("100.00"),
            "starting_price": Decimal("8.50"), "currency": "EUR", "duration": 21, "reserve": Decimal("12.00"),
            "description": "High-quality laboratory borosilicate glassware from university and research facility upgrades. Various sizes and types included.",
            "keywords": "laboratory, borosilicate, glassware, research, scientific"
        },
        {
            "title": "Food Grade Silicone Rubber Sheets",
            "category": "Plastics", "subcategory": "Other plastics",
            "specific_material": "FDA approved silicone rubber sheets from food processing",
            "packaging": "roles", "material_frequency": "monthly",
            "specification_type": "food_grade_sheets",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["calendering", "thermoforming"],
            "available_quantity": Decimal("500.00"), "unit": "m³", "min_order": Decimal("25.00"),
            "starting_price": Decimal("45.00"), "currency": "EUR", "duration": 10, "reserve": Decimal("65.00"),
            "description": "FDA food grade silicone rubber sheets suitable for food processing equipment and pharmaceutical applications. Heat resistant to 250°C.",
            "keywords": "silicone, food grade, FDA, heat resistant, pharmaceutical"
        },
        {
            "title": "High-Purity Aluminum Cans - Beverage Industry",
            "category": "Metals", "subcategory": "Aluminium",
            "specific_material": "Clean aluminum beverage cans from bottling facilities",
            "packaging": "baled", "material_frequency": "weekly",
            "specification_type": "beverage_aluminum",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("45000.00"), "unit": "pieces", "min_order": Decimal("5000.00"),
            "starting_price": Decimal("0.12"), "currency": "EUR", "duration": 7, "reserve": Decimal("0.18"),
            "description": "High-volume clean aluminum cans from major beverage producers. Sorted, compressed, and ready for recycling with high aluminum content.",
            "keywords": "aluminum, cans, beverage, high volume, recycling"
        },
        {
            "title": "Pharmaceutical Packaging Waste - PP Bottles",
            "category": "Plastics", "subcategory": "PP",
            "specific_material": "Pharmaceutical grade PP bottles and containers",
            "packaging": "big_bag", "material_frequency": "monthly",
            "specification_type": "pharmaceutical_pp",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["injection_moulding", "blow_moulding"],
            "available_quantity": Decimal("8500.00"), "unit": "units", "min_order": Decimal("500.00"),
            "starting_price": Decimal("0.35"), "currency": "EUR", "duration": 0, "custom_duration": 25, "reserve": Decimal("0.55"),
            "description": "Clean pharmaceutical grade PP bottles from medicine packaging. Labels removed, sorted by size, suitable for medical applications.",
            "keywords": "pharmaceutical, PP, bottles, medical grade, clean"
        },
        {
            "title": "Recycled Newspaper Pulp - High Quality",
            "category": "Paper", "subcategory": "Newspaper",
            "specific_material": "Processed newspaper pulp ready for paper manufacturing",
            "packaging": "container", "material_frequency": "weekly",
            "specification_type": "newsprint_pulp",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("15000.00"), "unit": "liters", "min_order": Decimal("1000.00"),
            "starting_price": Decimal("0.25"), "currency": "EUR", "duration": 7, "reserve": Decimal("0.35"),
            "description": "High-quality processed newspaper pulp in liquid form. De-inked and bleached, ready for paper manufacturing or packaging applications.",
            "keywords": "newspaper, pulp, processed, paper manufacturing, liquid"
        },
        {
            "title": "Industrial Hemp Fiber Bales",
            "category": "Textiles", "subcategory": "Other textiles",
            "specific_material": "Industrial hemp fiber for textile and construction applications",
            "packaging": "baled", "material_frequency": "quarterly",
            "specification_type": "hemp_fiber",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("200.00"), "unit": "bales", "min_order": Decimal("20.00"),
            "starting_price": Decimal("180.00"), "currency": "EUR", "duration": 0, "custom_duration": 28, "reserve": Decimal("220.00"),
            "description": "Premium industrial hemp fiber suitable for textiles, composites, and bio-based construction materials. Sustainably sourced and processed.",
            "keywords": "hemp, fiber, industrial, sustainable, composites"
        },
        {
            "title": "Electronic Circuit Board Gold Recovery",
            "category": "E-waste", "subcategory": "Small devices (max 50 cm)",
            "specific_material": "High-density circuit boards with precious metals",
            "packaging": "container", "material_frequency": "monthly",
            "specification_type": "precious_metals_pcb",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("750.00"), "unit": "pieces", "min_order": Decimal("50.00"),
            "starting_price": Decimal("25.00"), "currency": "EUR", "duration": 14, "reserve": Decimal("35.00"),
            "description": "High-value electronic circuit boards from telecommunications equipment. Rich in gold, silver, platinum, and palladium for precious metal recovery.",
            "keywords": "circuit boards, precious metals, gold recovery, telecommunications, WEEE"
        },
        {
            "title": "Marine Grade Stainless Steel Cable",
            "category": "Metals", "subcategory": "Stainless steel",
            "specific_material": "316L marine grade stainless steel cable and fittings",
            "packaging": "roles", "material_frequency": "quarterly",
            "specification_type": "marine_stainless",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("5000.00"), "unit": "meters", "min_order": Decimal("500.00"),
            "starting_price": Decimal("12.50"), "currency": "EUR", "duration": 21, "reserve": Decimal("18.00"),
            "description": "Premium 316L marine grade stainless steel cable from shipbuilding industry. Corrosion resistant, various diameters from 3mm to 20mm.",
            "keywords": "stainless steel, marine grade, cable, 316L, corrosion resistant"
        },
        {
            "title": "Biodegradable Packaging Films",
            "category": "Plastics", "subcategory": "Other plastics",
            "specific_material": "PLA and PHA biodegradable films from food packaging",
            "packaging": "roles", "material_frequency": "bi_weekly",
            "specification_type": "biodegradable_films",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["extrusion", "blow_moulding"],
            "available_quantity": Decimal("2500.00"), "unit": "m³", "min_order": Decimal("100.00"),
            "starting_price": Decimal("8.50"), "currency": "EUR", "duration": 0, "custom_duration": 10, "reserve": Decimal("12.00"),
            "description": "Compostable biodegradable films made from PLA and PHA. Suitable for eco-friendly packaging applications and agricultural mulch films.",
            "keywords": "biodegradable, PLA, PHA, compostable, eco-friendly"
        },
        {
            "title": "Architectural Glass Panels - Tempered",
            "category": "Glass", "subcategory": "Other glass",
            "specific_material": "Large tempered glass panels from building construction",
            "packaging": "container", "material_frequency": "yearly",
            "specification_type": "architectural_glass",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("850.00"), "unit": "m³", "min_order": Decimal("50.00"),
            "starting_price": Decimal("35.00"), "currency": "EUR", "duration": 0, "custom_duration": 42, "reserve": Decimal("50.00"),
            "description": "Large architectural tempered glass panels from building renovations. Various sizes, safety glass standard, suitable for reuse or recycling.",
            "keywords": "architectural glass, tempered, building, renovation, safety glass"
        },
        {
            "title": "Precision Aluminum Aerospace Shavings",
            "category": "Metals", "subcategory": "Aluminium",
            "specific_material": "High-purity aluminum shavings from CNC machining",
            "packaging": "container", "material_frequency": "weekly",
            "specification_type": "precision_aluminum",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("3200.00"), "unit": "kg", "min_order": Decimal("200.00"),
            "starting_price": Decimal("4.85"), "currency": "EUR", "duration": 7, "reserve": Decimal("6.50"),
            "description": "Ultra-high purity aluminum shavings from aerospace CNC machining operations. Various alloys including 6061, 7075, and 2024 grades.",
            "keywords": "aluminum, aerospace, CNC, shavings, high purity"
        },
        {
            "title": "Medical Device Plastic Components",
            "category": "Plastics", "subcategory": "Other plastics",
            "specific_material": "PEEK and PTFE components from medical device manufacturing",
            "packaging": "container", "material_frequency": "quarterly",
            "specification_type": "medical_device_plastics",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["injection_moulding", "sintering"],
            "available_quantity": Decimal("450.00"), "unit": "pieces", "min_order": Decimal("25.00"),
            "starting_price": Decimal("85.00"), "currency": "EUR", "duration": 0, "custom_duration": 30, "reserve": Decimal("120.00"),
            "description": "High-performance PEEK and PTFE components from medical device production. Biocompatible, sterilizable, and certified for medical applications.",
            "keywords": "PEEK, PTFE, medical device, biocompatible, sterilizable"
        },
        {
            "title": "Industrial Cardboard Cores and Tubes",
            "category": "Paper", "subcategory": "Cardboard",
            "specific_material": "Spiral wound cardboard cores from textile and paper industries",
            "packaging": "loose", "material_frequency": "weekly",
            "specification_type": "cardboard_cores",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("12000.00"), "unit": "pieces", "min_order": Decimal("500.00"),
            "starting_price": Decimal("1.25"), "currency": "EUR", "duration": 10, "reserve": Decimal("2.00"),
            "description": "Heavy-duty cardboard cores and tubes from textile and paper manufacturing. Various diameters and lengths, suitable for reuse or recycling.",
            "keywords": "cardboard, cores, tubes, textile, paper industry"
        },
        {
            "title": "Automotive Wiring Harness Copper",
            "category": "Metals", "subcategory": "Copper",
            "specific_material": "Copper wire from automotive wiring harnesses",
            "packaging": "baled", "material_frequency": "bi_weekly",
            "specification_type": "automotive_copper",
            "origin": "post_consumer", "contamination": "slightly_contaminated", "additives": "no_additives", "storage_conditions": "protected_outdoor",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("1850.00"), "unit": "kg", "min_order": Decimal("100.00"),
            "starting_price": Decimal("8.25"), "currency": "EUR", "duration": 14, "reserve": Decimal("9.50"),
            "description": "Copper wire recovered from automotive wiring harnesses. Mixed gauges, some insulation present, high copper content suitable for refining.",
            "keywords": "copper, automotive, wiring, harnesses, recycling"
        },
        {
            "title": "High-Tech Ceramic Components",
            "category": "Building material", "subcategory": "Other building materials",
            "specific_material": "Advanced ceramic components from electronics manufacturing",
            "packaging": "container", "material_frequency": "monthly",
            "specification_type": "advanced_ceramics",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("320.00"), "unit": "pieces", "min_order": Decimal("20.00"),
            "starting_price": Decimal("45.00"), "currency": "EUR", "duration": 0, "custom_duration": 21, "reserve": Decimal("65.00"),
            "description": "High-performance ceramic components including alumina, zirconia, and silicon carbide from electronics and aerospace applications.",
            "keywords": "ceramics, advanced, electronics, aerospace, high performance"
        },
        {
            "title": "Wool Textile Waste - Natural Fibers",
            "category": "Textiles", "subcategory": "Wool",
            "specific_material": "Pure wool textile waste from luxury fashion manufacturing",
            "packaging": "baled", "material_frequency": "monthly",
            "specification_type": "wool_waste",
            "origin": "post_industrial", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["calendering"],
            "available_quantity": Decimal("65.00"), "unit": "bales", "min_order": Decimal("5.00"),
            "starting_price": Decimal("250.00"), "currency": "EUR", "duration": 21, "reserve": Decimal("320.00"),
            "description": "Premium wool textile waste from luxury fashion houses. Various wool types including merino, cashmere, and alpaca. Perfect for high-end recycling.",
            "keywords": "wool, luxury, fashion, merino, cashmere"
        },
        {
            "title": "Solar Panel Silicon Wafers",
            "category": "E-waste", "subcategory": "Large devices (more than 50 cm)",
            "specific_material": "Silicon wafers and cells from end-of-life solar panels",
            "packaging": "container", "material_frequency": "quarterly",
            "specification_type": "solar_silicon",
            "origin": "post_consumer", "contamination": "clean", "additives": "no_additives", "storage_conditions": "climate_controlled",
            "processing_methods": ["sintering"],
            "available_quantity": Decimal("1200.00"), "unit": "pieces", "min_order": Decimal("100.00"),
            "starting_price": Decimal("15.00"), "currency": "EUR", "duration": 0, "custom_duration": 35, "reserve": Decimal("22.00"),
            "description": "High-purity silicon wafers and cells recovered from end-of-life solar panels. Suitable for silicon recovery and semiconductor applications.",
            "keywords": "solar panels, silicon, wafers, semiconductor, renewable energy"
        }
    ]
    
    # Clear existing ads
    Ad.objects.all().delete()
    print("  ✓ Cleared existing ads")
    
    created_ads = []
    
    for i, ad_data in enumerate(ads_data):
        try:
            # Get random user and location
            user = random.choice(users)
            location = random.choice(locations)
            
            # Get category and subcategory
            category = Category.objects.get(name=ad_data["category"])
            subcategory = SubCategory.objects.get(name=ad_data["subcategory"], category=category)
            
            # Get appropriate specification
            matching_specs = [spec for spec in specifications if spec.Category == category]
            specification = random.choice(matching_specs) if matching_specs else None
            
            # Create ad
            ad = Ad.objects.create(
                user=user,
                category=category,
                subcategory=subcategory,
                specific_material=ad_data["specific_material"],
                packaging=ad_data["packaging"],
                material_frequency=ad_data["material_frequency"],
                specification=specification,
                additional_specifications=specification.additional_specifications if specification else None,
                origin=ad_data["origin"],
                contamination=ad_data["contamination"],
                additives=ad_data["additives"],
                storage_conditions=ad_data["storage_conditions"],
                processing_methods=ad_data["processing_methods"],
                location=location,
                pickup_available=random.choice([True, False]),
                delivery_options=random.sample(["pickup_only", "local_delivery", "national_shipping", "international_shipping"], 
                                             random.randint(1, 3)),
                available_quantity=ad_data["available_quantity"],
                unit_of_measurement=ad_data["unit"],
                minimum_order_quantity=ad_data["min_order"],
                starting_bid_price=ad_data["starting_price"],
                currency=ad_data["currency"],
                auction_duration=ad_data["duration"],
                custom_auction_duration=ad_data.get("custom_duration"),
                reserve_price=ad_data.get("reserve"),
                title=ad_data["title"],
                description=ad_data["description"],
                keywords=ad_data["keywords"],
                current_step=8,
                is_complete=True,
                is_active=True,
                auction_start_date=timezone.now() - timedelta(days=random.randint(0, 5)),
                auction_end_date=timezone.now() + timedelta(days=ad_data.get("custom_duration", ad_data["duration"]))
            )
            
            created_ads.append(ad)
            print(f"  ✓ Created ad #{ad.id}: {ad.title}")
            
        except Exception as e:
            print(f"  ❌ Failed to create ad: {ad_data['title']} - {e}")
            continue
    
    print(f"\n✅ Created {len(created_ads)} realistic ads")
    return created_ads


def create_realistic_bids(ads):
    """Create 15+ realistic bids on the ads"""
    
    print("\n💰 Creating realistic bids...")
    
    # Get bidding users (exclude ad owners)
    all_users = list(User.objects.filter(is_superuser=False, company__isnull=False))
    
    # Clear existing bids
    Bid.objects.all().delete()
    print("  ✓ Cleared existing bids")
    
    created_bids = []
    
    # Select subset of ads for bidding
    bidding_ads = random.sample(ads, min(12, len(ads)))
    
    for ad in bidding_ads:
        # Get potential bidders (exclude ad owner)
        potential_bidders = [u for u in all_users if u != ad.user]
        
        # Create 1-3 bids per ad
        num_bids = random.randint(1, 3)
        selected_bidders = random.sample(potential_bidders, min(num_bids, len(potential_bidders)))
        
        base_price = ad.starting_bid_price
        current_price = base_price
        
        for j, bidder in enumerate(selected_bidders):
            # Calculate bid price (incremental)
            if j == 0:
                bid_price = base_price + Decimal(str(random.uniform(1, 10)))
            else:
                bid_price = current_price + Decimal(str(random.uniform(5, 25)))
            
            # Calculate volume (partial or full)
            volume_type = random.choice(["partial", "partial", "full"])  # Favor partial
            if volume_type == "full":
                volume = float(ad.available_quantity)
            else:
                volume = float(ad.available_quantity * Decimal(str(random.uniform(0.1, 0.7))))
            
            # Ensure minimum order quantity
            volume = max(volume, float(ad.minimum_order_quantity))
            
            try:
                bid = Bid.objects.create(
                    ad=ad,
                    user=bidder,
                    bid_price_per_unit=bid_price,
                    volume_requested=Decimal(str(volume)),
                    volume_type=volume_type,
                    notes=f"Competitive bid for {ad.title}",
                    max_auto_bid_price=bid_price + Decimal(str(random.uniform(10, 50))),
                    is_auto_bid=random.choice([True, False]),  # Fixed field name
                    created_at=timezone.now() - timedelta(hours=random.randint(1, 72))
                )
                
                created_bids.append(bid)
                current_price = bid_price
                print(f"  ✓ Created bid #{bid.id}: {bidder.username} -> €{bid_price}/{ad.unit_of_measurement} for {volume:.1f}{ad.unit_of_measurement}")
                
            except Exception as e:
                print(f"  ❌ Failed to create bid: {e}")
                continue
    
    print(f"\n✅ Created {len(created_bids)} realistic bids")
    return created_bids


def main():
    """Main function to create all test data"""
    
    print("🚀 Creating realistic ads and bids for Nordic Loop Platform...")
    print("=" * 60)
    
    # Create ads
    ads = create_realistic_ads()
    
    # Create bids
    bids = create_realistic_bids(ads)
    
    # Display summary
    print("\n" + "=" * 60)
    print("📊 CREATION SUMMARY")
    print("=" * 60)
    print(f"✅ Total Ads Created: {len(ads)}")
    print(f"✅ Total Bids Created: {len(bids)}")
    print(f"✅ Active Auctions: {Ad.objects.filter(is_active=True).count()}")
    print(f"✅ Completed Ads: {Ad.objects.filter(is_complete=True).count()}")
    
    # Category breakdown
    print("\n📈 CATEGORY BREAKDOWN:")
    for category in Category.objects.all():
        count = Ad.objects.filter(category=category).count()
        if count > 0:
            print(f"  {category.name}: {count} ads")
    
    # Location breakdown  
    print("\n🌍 LOCATION BREAKDOWN:")
    location_counts = {}
    for ad in ads:
        if ad.location:
            country = ad.location.country
            location_counts[country] = location_counts.get(country, 0) + 1
    
    for country, count in sorted(location_counts.items()):
        print(f"  {country}: {count} ads")
    
    # Price ranges
    print("\n💰 PRICE RANGES:")
    prices = [float(ad.starting_bid_price) for ad in ads]
    print(f"  Lowest: €{min(prices):.2f}")
    print(f"  Highest: €{max(prices):.2f}")
    print(f"  Average: €{sum(prices)/len(prices):.2f}")
    
    print("\n🎉 Realistic marketplace data creation completed!")
    print("\n🔗 Test the marketplace:")
    print("   GET /api/ads/                     - List all ads")
    print("   GET /api/ads/{id}/                - Get ad details")
    print("   GET /api/bids/ad/{ad_id}/         - List bids for ad")
    print("   GET /api/category/                - List categories")
    print("   GET /api/category/specification-choices/ - Get specification choices")


if __name__ == "__main__":
    main() 