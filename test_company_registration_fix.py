#!/usr/bin/env python
"""
Test script to verify the company registration fix
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from company.services.company_service import CompanyService
from company.repository.company_repository import CompanyRepository


def test_company_registration():
    """Test company registration with the same payload that was failing"""
    
    # Sample payload that was causing the error
    import time
    timestamp = str(int(time.time()))
    test_payload = {
        "official_name": "Test Company Fix",
        "vat_number": f"TEST{timestamp}",
        "email": f"test{timestamp}@testcompany.com",
        "website": "testcompany.com",
        "country": "Sweden",
        "sector": "manufacturing",
        "primary_first_name": "Olivier",
        "primary_last_name": "Karera",
        "primary_email": f"karera{timestamp}@testcompany.com",
        "primary_position": "Developer",
        "status": "pending",
        "secondary_first_name": "olivier2",
        "secondary_last_name": "karera2",
        "secondary_email": f"karera1{timestamp}@testcompany.com",
        "secondary_position": "CEO"
    }
    
    try:
        # Initialize service
        repository = CompanyRepository()
        service = CompanyService(repository)
        
        print("Testing company registration...")
        print(f"Payload: {test_payload}")
        
        # Create company
        company = service.create_company(test_payload)
        
        print(f"✅ SUCCESS: Company created successfully!")
        print(f"Company ID: {company.id}")
        print(f"Company Name: {company.official_name}")
        print(f"Company VAT: {company.vat_number}")
        print(f"Company Status: {company.status}")
        
        # Check if users were created
        from users.models import User
        primary_user = User.objects.filter(email=test_payload['primary_email']).first()
        secondary_user = User.objects.filter(email=test_payload['secondary_email']).first()
        
        if primary_user:
            print(f"✅ Primary contact user created: {primary_user.email}")
            print(f"   - Bank Country: {primary_user.bank_country}")
            print(f"   - Contact Type: {primary_user.contact_type}")
            print(f"   - Is Primary: {primary_user.is_primary_contact}")
        
        if secondary_user:
            print(f"✅ Secondary contact user created: {secondary_user.email}")
            print(f"   - Bank Country: {secondary_user.bank_country}")
            print(f"   - Contact Type: {secondary_user.contact_type}")
            print(f"   - Is Primary: {secondary_user.is_primary_contact}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    success = test_company_registration()
    sys.exit(0 if success else 1)
