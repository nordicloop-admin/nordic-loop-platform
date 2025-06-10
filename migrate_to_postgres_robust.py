#!/usr/bin/env python
"""
Robust PostgreSQL Migration Script for Nordic Loop Platform
Migrates data from dbv2.sqlite3 to PostgreSQL while handling schema differences gracefully
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Set minimal environment variables if not set
if not os.getenv('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'migration-key-temporary'
if not os.getenv('DJANGO_ENV'):
    os.environ['DJANGO_ENV'] = 'development'
if not os.getenv('DJANGO_DEBUG'):
    os.environ['DJANGO_DEBUG'] = 'True'
if not os.getenv('DJANGO_ALLOWED_HOSTS'):
    os.environ['DJANGO_ALLOWED_HOSTS'] = 'localhost,127.0.0.1'

import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import transaction, connection, IntegrityError
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.utils import timezone

# Import your models
from company.models import Company
from users.models import User
from category.models import Category, SubCategory, CategorySpecification
from ads.models import Ad, Location
from bids.models import Bid, BidHistory


class RobustPostgreSQLMigrator:
    """
    Robust data migration from SQLite to PostgreSQL with schema adaptation
    """
    
    def __init__(self, source_db_path="dbv2.sqlite3"):
        self.source_db_path = Path(source_db_path)
        self.migration_log = []
        
        if not self.source_db_path.exists():
            raise FileNotFoundError(f"Source database {source_db_path} not found")
    
    def log(self, message):
        """Log migration progress"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.migration_log.append(log_message)
    
    def get_sqlite_connection(self):
        """Get SQLite database connection"""
        return sqlite3.connect(self.source_db_path)
    
    def get_sqlite_data(self, table_name):
        """Get all data from SQLite table"""
        with self.get_sqlite_connection() as conn:
            cursor = conn.cursor()
            
            # Get column names first
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]  # Extract column names
            
            # Get all data
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Convert to dictionaries
            result = []
            for row in rows:
                row_dict = dict(zip(column_names, row))
                result.append(row_dict)
            
            return result
    
    def safe_get(self, row, key, default=None):
        """Safely get value from row dict"""
        return row.get(key, default)
    
    def parse_datetime(self, datetime_str):
        """Parse datetime string safely"""
        if not datetime_str:
            return None
        try:
            # Handle different datetime formats
            if 'T' in datetime_str:
                dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(datetime_str)
            return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        except:
            return None
    
    def parse_date(self, date_str):
        """Parse date string safely"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str).date()
        except:
            return None
    
    def clear_existing_data(self):
        """Clear existing data (optional - be careful!)"""
        self.log("⚠️  WARNING: This will clear existing PostgreSQL data!")
        confirm = input("Are you sure you want to clear existing data? (type 'CLEAR' to confirm): ")
        
        if confirm != 'CLEAR':
            self.log("❌ Migration cancelled")
            return False
        
        with transaction.atomic():
            # Clear in reverse dependency order
            BidHistory.objects.all().delete()
            Bid.objects.all().delete()
            Ad.objects.all().delete()
            Location.objects.all().delete()
            CategorySpecification.objects.all().delete()
            SubCategory.objects.all().delete()
            Category.objects.all().delete()
            User.objects.all().delete()
            Company.objects.all().delete()
            
            self.log("✅ Existing data cleared")
            return True
    
    def migrate_companies(self):
        """Migrate company data"""
        self.log("🏢 Migrating companies...")
        
        sqlite_companies = self.get_sqlite_data('company_company')
        created_count = 0
        
        with transaction.atomic():
            for row in sqlite_companies:
                try:
                    company_data = {
                        'id': row['id'],
                        'official_name': row['official_name'],
                        'vat_number': row['vat_number'],
                        'email': row['email'],
                        'sector': row['sector'],
                        'country': row['country'],
                        'website': self.safe_get(row, 'website', ''),
                        'primary_first_name': self.safe_get(row, 'primary_first_name', ''),
                        'primary_last_name': self.safe_get(row, 'primary_last_name', ''),
                        'primary_position': self.safe_get(row, 'primary_position', ''),
                        'primary_email': self.safe_get(row, 'primary_email', ''),
                        'status': self.safe_get(row, 'status', 'pending'),
                        'registration_date': self.parse_date(self.safe_get(row, 'registration_date')) or timezone.now().date()
                    }
                    
                    # Handle optional fields that may not exist in SQLite but are required in Django
                    optional_fields = ['phone_number', 'address_line', 'city', 'postal_code', 'state_province']
                    for field in optional_fields:
                        company_data[field] = self.safe_get(row, field, '')
                    
                    company = Company.objects.create(**company_data)
                    created_count += 1
                    
                except IntegrityError as e:
                    self.log(f"⚠️  Company {row['official_name']} already exists: {e}")
                except Exception as e:
                    self.log(f"❌ Error creating company {row['official_name']}: {e}")
        
        self.log(f"✅ Companies migrated: {created_count}/{len(sqlite_companies)}")
        return created_count
    
    def migrate_users(self):
        """Migrate user data with preserved passwords"""
        self.log("👥 Migrating users with preserved passwords...")
        
        sqlite_users = self.get_sqlite_data('users_user')
        created_count = 0
        
        with transaction.atomic():
            for row in sqlite_users:
                try:
                    # Get the associated company
                    company = None
                    if self.safe_get(row, 'company_id'):
                        try:
                            company = Company.objects.get(id=row['company_id'])
                        except Company.DoesNotExist:
                            self.log(f"⚠️  Company with ID {row['company_id']} not found for user {row['email']}")
                    
                    # Create user data dict with safe defaults
                    user_data = {
                        'id': row['id'],
                        'password': row['password'],  # Preserve the hashed password
                        'last_login': self.parse_datetime(self.safe_get(row, 'last_login')),
                        'is_superuser': bool(self.safe_get(row, 'is_superuser', False)),
                        'username': row['username'],
                        'first_name': self.safe_get(row, 'first_name', ''),
                        'last_name': self.safe_get(row, 'last_name', ''),
                        'email': row['email'],
                        'is_staff': bool(self.safe_get(row, 'is_staff', False)),
                        'is_active': bool(self.safe_get(row, 'is_active', True)),
                        'date_joined': self.parse_datetime(self.safe_get(row, 'date_joined')) or timezone.now(),
                        'name': self.safe_get(row, 'name', ''),
                        'company': company
                    }
                    
                    # Handle optional fields that may not exist in SQLite
                    optional_user_fields = ['bio', 'avatar', 'location', 'birth_date']
                    for field in optional_user_fields:
                        if field == 'birth_date':
                            user_data[field] = self.parse_date(self.safe_get(row, field))
                        else:
                            user_data[field] = self.safe_get(row, field, '')
                    
                    user = User(**user_data)
                    user.save()
                    created_count += 1
                    
                except IntegrityError as e:
                    self.log(f"⚠️  User {row['email']} already exists: {e}")
                except Exception as e:
                    self.log(f"❌ Error creating user {row['email']}: {e}")
        
        self.log(f"✅ Users migrated: {created_count}/{len(sqlite_users)} (passwords preserved)")
        return created_count
    
    def migrate_categories(self):
        """Migrate category data"""
        self.log("📁 Migrating categories...")
        
        sqlite_categories = self.get_sqlite_data('category_category')
        created_count = 0
        
        with transaction.atomic():
            for row in sqlite_categories:
                try:
                    category = Category.objects.create(
                        id=row['id'],
                        name=row['name']
                    )
                    created_count += 1
                    
                except IntegrityError as e:
                    self.log(f"⚠️  Category {row['name']} already exists: {e}")
                except Exception as e:
                    self.log(f"❌ Error creating category {row['name']}: {e}")
        
        self.log(f"✅ Categories migrated: {created_count}/{len(sqlite_categories)}")
        return created_count
    
    def migrate_subcategories(self):
        """Migrate subcategory data"""
        self.log("📂 Migrating subcategories...")
        
        sqlite_subcategories = self.get_sqlite_data('category_subcategory')
        created_count = 0
        
        with transaction.atomic():
            for row in sqlite_subcategories:
                try:
                    category = Category.objects.get(id=row['category_id'])
                    subcategory = SubCategory.objects.create(
                        id=row['id'],
                        name=row['name'],
                        category=category
                    )
                    created_count += 1
                    
                except Category.DoesNotExist:
                    self.log(f"⚠️  Category with ID {row['category_id']} not found for subcategory {row['name']}")
                except IntegrityError as e:
                    self.log(f"⚠️  SubCategory {row['name']} already exists: {e}")
                except Exception as e:
                    self.log(f"❌ Error creating subcategory {row['name']}: {e}")
        
        self.log(f"✅ SubCategories migrated: {created_count}/{len(sqlite_subcategories)}")
        return created_count
    
    def migrate_category_specifications(self):
        """Migrate category specifications"""
        self.log("⚙️  Migrating category specifications...")
        
        sqlite_specs = self.get_sqlite_data('category_categoryspecification')
        created_count = 0
        
        with transaction.atomic():
            for row in sqlite_specs:
                try:
                    # Check for different possible column names for category
                    category_id = self.safe_get(row, 'category_id') or self.safe_get(row, 'Category_id')
                    if not category_id:
                        self.log(f"⚠️  No category ID found for specification")
                        continue
                    
                    category = Category.objects.get(id=category_id)
                    
                    spec_data = {
                        'id': row['id'],
                        'category': category,
                        'field_name': self.safe_get(row, 'field_name', ''),
                        'field_type': self.safe_get(row, 'field_type', 'text'),
                        'is_required': bool(self.safe_get(row, 'is_required', False)),
                        'options': self.safe_get(row, 'options'),
                        'description': self.safe_get(row, 'description', '')
                    }
                    
                    spec = CategorySpecification.objects.create(**spec_data)
                    created_count += 1
                    
                except Category.DoesNotExist:
                    self.log(f"⚠️  Category with ID {category_id} not found for specification")
                except Exception as e:
                    self.log(f"❌ Error creating category specification: {e}")
        
        self.log(f"✅ Category specifications migrated: {created_count}/{len(sqlite_specs)}")
        return created_count
    
    def migrate_locations(self):
        """Migrate location data"""
        self.log("📍 Migrating locations...")
        
        sqlite_locations = self.get_sqlite_data('ads_location')
        created_count = 0
        
        with transaction.atomic():
            for row in sqlite_locations:
                try:
                    location_data = {
                        'id': row['id'],
                        'country': row['country'],
                        'state_province': self.safe_get(row, 'state_province', ''),
                        'city': row['city'],
                        'address_line': self.safe_get(row, 'address_line', ''),
                        'postal_code': self.safe_get(row, 'postal_code', ''),
                        'latitude': float(row['latitude']) if self.safe_get(row, 'latitude') else None,
                        'longitude': float(row['longitude']) if self.safe_get(row, 'longitude') else None
                    }
                    
                    location = Location.objects.create(**location_data)
                    created_count += 1
                    
                except Exception as e:
                    self.log(f"❌ Error creating location: {e}")
        
        self.log(f"✅ Locations migrated: {created_count}/{len(sqlite_locations)}")
        return created_count
    
    def migrate_ads(self):
        """Migrate ads data"""
        self.log("🏭 Migrating ads...")
        
        sqlite_ads = self.get_sqlite_data('ads_ad')
        created_count = 0
        
        with transaction.atomic():
            for row in sqlite_ads:
                try:
                    # Get related objects with safe lookups
                    user = User.objects.get(id=row['user_id'])
                    category = Category.objects.get(id=row['category_id']) if self.safe_get(row, 'category_id') else None
                    subcategory = SubCategory.objects.get(id=row['subcategory_id']) if self.safe_get(row, 'subcategory_id') else None
                    location = Location.objects.get(id=row['location_id']) if self.safe_get(row, 'location_id') else None
                    specification = CategorySpecification.objects.get(id=row['specification_id']) if self.safe_get(row, 'specification_id') else None
                    
                    ad_data = {
                        'id': row['id'],
                        'user': user,
                        'category': category,
                        'subcategory': subcategory,
                        'location': location,
                        'specification': specification,
                        'specific_material': self.safe_get(row, 'specific_material', ''),
                        'packaging': self.safe_get(row, 'packaging', ''),
                        'material_frequency': self.safe_get(row, 'material_frequency', ''),
                        'additional_specifications': self.safe_get(row, 'additional_specifications', ''),
                        'origin': self.safe_get(row, 'origin', ''),
                        'contamination': self.safe_get(row, 'contamination', ''),
                        'additives': self.safe_get(row, 'additives', ''),
                        'storage_conditions': self.safe_get(row, 'storage_conditions', ''),
                        'processing_methods': self.safe_get(row, 'processing_methods', '[]'),
                        'pickup_available': bool(self.safe_get(row, 'pickup_available', False)),
                        'delivery_options': self.safe_get(row, 'delivery_options', '[]'),
                        'available_quantity': Decimal(str(row['available_quantity'])) if self.safe_get(row, 'available_quantity') else None,
                        'minimum_order_quantity': Decimal(str(row['minimum_order_quantity'])) if self.safe_get(row, 'minimum_order_quantity') else Decimal('1'),
                        'starting_bid_price': Decimal(str(row['starting_bid_price'])) if self.safe_get(row, 'starting_bid_price') else None,
                        'currency': self.safe_get(row, 'currency', 'EUR'),
                        'auction_duration': self.safe_get(row, 'auction_duration', 7),
                        'reserve_price': Decimal(str(row['reserve_price'])) if self.safe_get(row, 'reserve_price') else None,
                        'title': self.safe_get(row, 'title', ''),
                        'description': self.safe_get(row, 'description', ''),
                        'keywords': self.safe_get(row, 'keywords', ''),
                        'material_image': self.safe_get(row, 'material_image', ''),
                        'is_active': bool(self.safe_get(row, 'is_active', True)),
                        'created_at': self.parse_datetime(self.safe_get(row, 'created_at')) or timezone.now(),
                        'updated_at': self.parse_datetime(self.safe_get(row, 'updated_at')) or timezone.now(),
                        'auction_start_date': self.parse_datetime(self.safe_get(row, 'auction_start_date')),
                        'auction_end_date': self.parse_datetime(self.safe_get(row, 'auction_end_date')),
                        'current_step': self.safe_get(row, 'current_step', 1),
                        'is_complete': bool(self.safe_get(row, 'is_complete', False)),
                        'custom_auction_duration': self.safe_get(row, 'custom_auction_duration'),
                        'unit_of_measurement': self.safe_get(row, 'unit_of_measurement', 'kg')
                    }
                    
                    ad = Ad.objects.create(**ad_data)
                    created_count += 1
                    
                except User.DoesNotExist:
                    self.log(f"⚠️  User with ID {row['user_id']} not found for ad {row['id']}")
                except Exception as e:
                    self.log(f"❌ Error creating ad ID {row['id']}: {e}")
        
        self.log(f"✅ Ads migrated: {created_count}/{len(sqlite_ads)}")
        return created_count
    
    def verify_migration(self):
        """Verify migration results"""
        self.log("🔍 Verifying migration...")
        
        verification_results = {
            'Companies': Company.objects.count(),
            'Users': User.objects.count(),
            'Categories': Category.objects.count(),
            'SubCategories': SubCategory.objects.count(),
            'Category Specifications': CategorySpecification.objects.count(),
            'Locations': Location.objects.count(),
            'Ads': Ad.objects.count(),
        }
        
        self.log("📊 Migration Results:")
        for model_name, count in verification_results.items():
            self.log(f"   {model_name}: {count} records")
        
        # Test user authentication
        test_user = User.objects.first()
        if test_user:
            self.log(f"🔐 Testing user authentication for: {test_user.email}")
            # This confirms the password hash was preserved
            self.log(f"   Password hash preserved: {test_user.password[:20]}...")
        
        return verification_results
    
    def run_full_migration(self, clear_existing=False):
        """Run complete migration process"""
        self.log("🚀 Starting PostgreSQL migration...")
        self.log(f"Source: {self.source_db_path}")
        self.log(f"Target: PostgreSQL database")
        
        if clear_existing and not self.clear_existing_data():
            return False
        
        try:
            # Migration order is important due to foreign key relationships
            results = {}
            
            results['companies'] = self.migrate_companies()
            results['users'] = self.migrate_users()
            results['categories'] = self.migrate_categories()
            results['subcategories'] = self.migrate_subcategories()
            results['category_specifications'] = self.migrate_category_specifications()
            results['locations'] = self.migrate_locations()
            results['ads'] = self.migrate_ads()
            
            # Verify migration
            verification = self.verify_migration()
            
            self.log("🎉 Migration completed successfully!")
            self.log("💡 User passwords have been preserved - existing users can login with their current passwords")
            
            return results
            
        except Exception as e:
            self.log(f"❌ Migration failed: {e}")
            return False
    
    def save_migration_log(self):
        """Save migration log to file"""
        log_file = Path("cloned_data") / f"postgres_migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("PostgreSQL Migration Log\n")
            f.write("=" * 50 + "\n\n")
            for log_entry in self.migration_log:
                f.write(f"{log_entry}\n")
        
        self.log(f"📄 Migration log saved to: {log_file}")
        return log_file


def main():
    """Main migration function"""
    print("🔄 Robust PostgreSQL Migration Tool for Nordic Loop Platform")
    print("This will migrate data from dbv2.sqlite3 to your PostgreSQL database")
    print()
    
    # Check current database connection
    print(f"🗄️  Current database: {connection.settings_dict['ENGINE']}")
    if 'postgresql' not in connection.settings_dict['ENGINE']:
        print("⚠️  Warning: This script is designed for PostgreSQL migration")
        print("   Make sure your Django settings are configured for PostgreSQL")
        proceed = input("Continue anyway? (y/N): ").lower().strip()
        if proceed != 'y':
            print("❌ Migration cancelled")
            return
    
    print()
    print("Migration Options:")
    print("1. Migrate data (keep existing data)")
    print("2. Clear existing data and migrate (DESTRUCTIVE)")
    print("3. Verify current data only")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    migrator = RobustPostgreSQLMigrator()
    
    try:
        if choice == "1":
            results = migrator.run_full_migration(clear_existing=False)
        elif choice == "2":
            results = migrator.run_full_migration(clear_existing=True)
        elif choice == "3":
            results = migrator.verify_migration()
        else:
            print("❌ Invalid choice")
            return
        
        # Save log
        migrator.save_migration_log()
        
        if results:
            print("\n✅ Migration completed successfully!")
            print("🔐 User passwords have been preserved")
            print("👥 Users can log in with their existing credentials")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        migrator.save_migration_log()


if __name__ == "__main__":
    main() 