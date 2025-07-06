#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from users.models import User
from company.models import Company

def main():
    try:
        # Get our test user
        user = User.objects.get(id=9)
        print(f"Working with user: {user.username}")
        
        # Create a test company
        company = Company.objects.create(
            official_name='Test Company',
            vat_number='TEST12345',
            email='test@company.com',
            primary_email='test@primary.com',
            country='Sweden',
            status='pending'
        )
        
        # Assign company to user
        user.company = company
        user.save()
        
        print(f"Company created and assigned: {company.official_name} (Status: {company.status})")
        
    except User.DoesNotExist:
        print("User with ID 9 not found")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 