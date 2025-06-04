#!/usr/bin/env python
"""
Setup script for Nordic Loop testing data
Run this script to create test users, categories, and companies for API testing
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from category.models import Category, SubCategory
from company.models import Company

User = get_user_model()

def create_test_data():
    print("🚀 Setting up test data for Nordic Loop Platform...")
    
    # Create test company
    company, created = Company.objects.get_or_create(
        primary_email="test@nordicloop.com",
        defaults={
            "official_name": "Test Nordic Company AB",
            "vat_number": "SE123456789",
            "email": "company@nordicloop.com",
            "sector": "recycling",
            "country": "Sweden",
            "website": "https://test.nordicloop.com",
            "primary_first_name": "John",
            "primary_last_name": "Doe",
            "primary_position": "CEO",
            "status": "approved"
        }
    )
    
    if created:
        print(f"✅ Created test company: {company.official_name}")
    else:
        print(f"📋 Company already exists: {company.official_name}")
    
    # Create test user
    user, created = User.objects.get_or_create(
        email="test@nordicloop.com",
        defaults={
            "username": "testuser",
            "name": "John Doe",
            "company": company
        }
    )
    
    if created:
        user.set_password("testpass123")
        user.save()
        print(f"✅ Created test user: {user.username}")
    else:
        print(f"📋 User already exists: {user.username}")
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        email="admin@nordicloop.com",
        defaults={
            "username": "admin",
            "name": "Admin User",
            "is_staff": True,
            "is_superuser": True,
            "role": "staff"
        }
    )
    
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        print(f"✅ Created admin user: {admin_user.username}")
    else:
        print(f"📋 Admin user already exists: {admin_user.username}")
    
    # Create categories
    categories_data = [
        {
            "name": "Plastics",
            "subcategories": ["PP", "HDPE", "PET", "LDPE", "PS", "PVC", "Other"]
        },
        {
            "name": "Paper",
            "subcategories": ["Cardboard", "Office Paper", "Newspaper", "Mixed Paper"]
        },
        {
            "name": "Metals", 
            "subcategories": ["Aluminum", "Steel", "Copper", "Mixed Metals"]
        },
        {
            "name": "Glass",
            "subcategories": ["Clear Glass", "Colored Glass", "Mixed Glass"]
        },
        {
            "name": "Textiles",
            "subcategories": ["Cotton", "Polyester", "Mixed Fabrics"]
        }
    ]
    
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            name=cat_data["name"]
        )
        
        if created:
            print(f"✅ Created category: {category.name}")
        else:
            print(f"📋 Category already exists: {category.name}")
        
        # Create subcategories
        for subcat_name in cat_data["subcategories"]:
            subcat, created = SubCategory.objects.get_or_create(
                name=subcat_name,
                category=category
            )
            
            if created:
                print(f"  ✅ Created subcategory: {subcat.name}")
    
    print("\n🎉 Test data setup complete!")
    print("\n📝 Use these credentials for testing:")
    print(f"   Email: test@nordicloop.com")
    print(f"   Password: testpass123")
    print(f"   Admin Email: admin@nordicloop.com")
    print(f"   Admin Password: admin123")
    print(f"\n🔗 Login endpoint: POST http://localhost:8000/api/users/login/")
    print(f"🔗 Ads endpoints: http://localhost:8000/api/ads/")

if __name__ == "__main__":
    create_test_data() 