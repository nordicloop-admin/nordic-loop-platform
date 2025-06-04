#!/usr/bin/env python
"""
Reset Sample Data Script for Nordic Loop Platform
Cleans up all sample data created by the sample data script
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
from ads.models import Ad, Location
from bids.models import Bid

User = get_user_model()

def reset_sample_data():
    """Remove all sample data except basic categories and the original test user"""
    print("🧹 Resetting sample data...")
    print("=" * 50)
    
    # Count before deletion
    print("📊 Current counts:")
    print(f"   👥 Users: {User.objects.count()}")
    print(f"   🏢 Companies: {Company.objects.count()}")
    print(f"   📍 Locations: {Location.objects.count()}")
    print(f"   🏭 Ads: {Ad.objects.count()}")
    print(f"   💰 Bids: {Bid.objects.count()}")
    
    # Delete bids first (due to foreign key relationships)
    bid_count = Bid.objects.count()
    Bid.objects.all().delete()
    print(f"🗑️  Deleted {bid_count} bids")
    
    # Delete ads
    ad_count = Ad.objects.count()
    Ad.objects.all().delete()
    print(f"🗑️  Deleted {ad_count} ads")
    
    # Delete locations
    location_count = Location.objects.count()
    Location.objects.all().delete()
    print(f"🗑️  Deleted {location_count} locations")
    
    # Delete sample companies (keep the original test one)
    sample_companies = Company.objects.exclude(primary_email="test@nordicloop.com")
    company_count = sample_companies.count()
    sample_companies.delete()
    print(f"🗑️  Deleted {company_count} sample companies")
    
    # Delete sample users (keep the original test and admin users)
    sample_users = User.objects.exclude(
        email__in=["test@nordicloop.com", "admin@nordicloop.com"]
    )
    user_count = sample_users.count()
    sample_users.delete()
    print(f"🗑️  Deleted {user_count} sample users")
    
    print("\n" + "=" * 50)
    print("✅ Sample data reset complete!")
    print("📊 Remaining counts:")
    print(f"   👥 Users: {User.objects.count()}")
    print(f"   🏢 Companies: {Company.objects.count()}")
    print(f"   📍 Locations: {Location.objects.count()}")
    print(f"   🏭 Ads: {Ad.objects.count()}")
    print(f"   💰 Bids: {Bid.objects.count()}")

def reset_everything():
    """Reset ALL data including basic test data"""
    print("⚠️  DANGER: Resetting ALL data including test users and categories!")
    print("=" * 60)
    
    # Delete all data
    Bid.objects.all().delete()
    Ad.objects.all().delete()
    Location.objects.all().delete()
    
    # Delete all users except superusers
    User.objects.filter(is_superuser=False).delete()
    
    # Delete all companies
    Company.objects.all().delete()
    
    print("🗑️  Deleted ALL sample and test data")
    print("✅ Complete reset finished - only Django superusers remain")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        confirmation = input("⚠️  This will delete ALL data. Type 'DELETE ALL' to confirm: ")
        if confirmation == "DELETE ALL":
            reset_everything()
        else:
            print("❌ Reset cancelled")
    else:
        reset_sample_data()
        print("\n💡 Tip: Use 'python reset_sample_data.py --all' to reset everything") 