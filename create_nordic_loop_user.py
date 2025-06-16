#!/usr/bin/env python3

import os
import django
from pathlib import Path
import secrets
import string

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import sys
sys.path.append(str(BASE_DIR))

django.setup()

from users.models import User
from company.models import Company

def generate_secure_password(length=12):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def create_nordic_loop_company_and_user():
    """Create Nordic Loop company and CEO user"""
    
    print("🚀 Creating Nordic Loop Company and CEO User...")
    print("=" * 60)
    
    # Company details
    company_data = {
        "official_name": "Nordic Loop",
        "vat_number": "SE556123456789",  # Swedish VAT format
        "email": "hello@nordicloop.se",
        "primary_email": "rahimianshaya@gmail.com",
        "primary_first_name": "Shaya",
        "primary_last_name": "Rahimian",
        "primary_position": "CEO & Founder",
        "secondary_first_name": "",
        "secondary_last_name": "",
        "secondary_email": "",
        "secondary_position": "",
        "sector": "recycling",  # Recycling & Waste Management sector
        "country": "Sweden",
        "website": "https://nordicloop.se",
        "status": "approved"  # Pre-approve the company
    }
    
    try:
        # Check if company already exists
        existing_company = Company.objects.filter(
            primary_email="rahimianshaya@gmail.com"
        ).first()
        
        if existing_company:
            print(f"⚠️  Company already exists: {existing_company.official_name}")
            company = existing_company
        else:
            # Create the company
            company = Company.objects.create(**company_data)
            print(f"✅ Created company: {company.official_name}")
            print(f"   VAT Number: {company.vat_number}")
            print(f"   Email: {company.email}")
            print(f"   Primary Contact: {company.primary_first_name} {company.primary_last_name}")
            print(f"   Website: {company.website}")
            print(f"   Status: {company.status}")
        
        # User details
        username = "shayarahimian"
        email = "rahimianshaya@gmail.com"
        password = generate_secure_password(16)  # Strong password for CEO
        
        # Check if user already exists
        existing_user = User.objects.filter(email=email).first()
        
        if existing_user:
            print(f"⚠️  User already exists: {existing_user.username}")
            user = existing_user
            # Update user details if needed
            user.first_name = "Shaya"
            user.last_name = "Rahimian"
            user.name = "Shaya Rahimian"
            user.company = company
            user.role = "Admin"  # CEO gets Admin role
            user.can_place_ads = True
            user.can_place_bids = True
            user.is_staff = True  # CEO has staff access
            user.is_superuser = True  # CEO gets superuser access
            user.save()
            print("✅ Updated existing user with CEO privileges")
        else:
            # Create the user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name="Shaya",
                last_name="Rahimian",
                name="Shaya Rahimian",
                company=company,
                role="Admin",  # CEO gets Admin role
                can_place_ads=True,
                can_place_bids=True,
                is_staff=True,  # CEO has staff access
                is_superuser=True  # CEO gets superuser access
            )
            print(f"✅ Created CEO user: {user.username}")
            print(f"   Email: {user.email}")
            print(f"   Full Name: {user.first_name} {user.last_name}")
            print(f"   Role: {user.role}")
            print(f"   Company: {user.company.official_name}")
            print(f"   Can Place Ads: {user.can_place_ads}")
            print(f"   Can Place Bids: {user.can_place_bids}")
            print(f"   Is Staff: {user.is_staff}")
            print(f"   Is Superuser: {user.is_superuser}")
            print(f"   Password: {password}")
        
        print("\n" + "=" * 60)
        print("🎉 Nordic Loop Setup Complete!")
        print("\n📋 LOGIN CREDENTIALS:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        if not existing_user:
            print(f"   Password: {password}")
        else:
            print("   Password: (unchanged - existing user)")
        print("\n🏢 COMPANY DETAILS:")
        print(f"   Company: {company.official_name}")
        print(f"   Website: {company.website}")
        print(f"   VAT Number: {company.vat_number}")
        print(f"   Status: {company.status}")
        
        # Save credentials to file for reference
        credentials_content = f"""
Nordic Loop CEO Login Credentials
================================
Username: {user.username}
Email: {user.email}
Password: {password if not existing_user else '(unchanged - existing user)'}
Role: CEO & Founder
Company: {company.official_name}
Website: {company.website}
Created: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'date_joined') else 'N/A'}
"""
        
        if not existing_user:
            with open('nordic_loop_credentials.txt', 'w') as f:
                f.write(credentials_content)
            print(f"\n💾 Credentials saved to: nordic_loop_credentials.txt")
        
        return user, company
        
    except Exception as e:
        print(f"❌ Error creating Nordic Loop setup: {e}")
        return None, None

if __name__ == "__main__":
    user, company = create_nordic_loop_company_and_user()
    
    if user and company:
        print("\n✅ Script completed successfully!")
    else:
        print("\n❌ Script failed!") 