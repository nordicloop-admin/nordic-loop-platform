#!/usr/bin/env python
"""
Test PostgreSQL Setup for Nordic Loop Platform
"""

import os
import sys

# Set minimal environment variables if not set
if not os.getenv('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'test-key-for-migration'
if not os.getenv('DJANGO_ENV'):
    os.environ['DJANGO_ENV'] = 'development'
if not os.getenv('DJANGO_DEBUG'):
    os.environ['DJANGO_DEBUG'] = 'True'
if not os.getenv('DJANGO_ALLOWED_HOSTS'):
    os.environ['DJANGO_ALLOWED_HOSTS'] = 'localhost,127.0.0.1'

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

try:
    import django
    django.setup()
    
    from django.db import connection
    from django.core.management import call_command
    
    print("✅ Django setup successful")
    print(f"🗄️  Database engine: {connection.settings_dict['ENGINE']}")
    print(f"🗄️  Database name: {connection.settings_dict.get('NAME', 'Not specified')}")
    
    # Test database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure your PostgreSQL database is running and DATABASE_URL is set")
        sys.exit(1)
    
    # Check if we have the required models
    try:
        from company.models import Company
        from users.models import User
        from category.models import Category, SubCategory
        from ads.models import Ad, Location
        from bids.models import Bid
        print("✅ All models imported successfully")
    except Exception as e:
        print(f"❌ Model import failed: {e}")
        sys.exit(1)
    
    print("🎉 PostgreSQL setup is ready for migration!")
    print("🚀 You can now run: python migrate_to_postgres.py")
    
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    print("💡 Check your environment variables and database configuration")
    sys.exit(1) 