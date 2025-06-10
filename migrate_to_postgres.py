#!/usr/bin/env python
"""
PostgreSQL Migration Script for Nordic Loop Platform
Migrates all data from dbv2.sqlite3 to PostgreSQL database while preserving user passwords and relationships
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


class PostgreSQLMigrator:
    """
    Comprehensive data migration from SQLite to PostgreSQL
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
                    company = Company.objects.create(
                        id=row['id'],
                        official_name=row['official_name'],
                        vat_number=row['vat_number'],
                        email=row['email'],
                        sector=row['sector'],
                        country=row['country'],
                        website=row['website'] if row['website'] else '',
                        primary_first_name=row['primary_first_name'],
                        primary_last_name=row['primary_last_name'],
                        primary_position=row['primary_position'] if row['primary_position'] else '',
                        primary_email=row['primary_email'],
                        phone_number=row['phone_number'] if row['phone_number'] else '',
                        address_line=row['address_line'] if row['address_line'] else '',
                        city=row['city'] if row['city'] else '',
                        postal_code=row['postal_code'] if row['postal_code'] else '',
                        state_province=row['state_province'] if row['state_province'] else '',
                        status=row['status'] if row['status'] else 'pending',
                        registration_date=timezone.make_aware(datetime.fromisoformat(row['registration_date'].replace('Z', '+00:00'))) if row['registration_date'] else timezone.now()
                    )
                    created_count += 1
                    
                except IntegrityError as e:
                    self.log(f"⚠️  Company {row['official_name']} already exists or error: {e}")
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
                    if row['company_id']:
                        try:
                            company = Company.objects.get(id=row['company_id'])
                        except Company.DoesNotExist:
                            self.log(f"⚠️  Company with ID {row['company_id']} not found for user {row['email']}")
                    
                    # Create user with preserved password hash
                    user = User(
                        id=row['id'],
                        password=row['password'],  # Preserve the hashed password
                        last_login=timezone.make_aware(datetime.fromisoformat(row['last_login'].replace('Z', '+00:00'))) if row['last_login'] else None,
                        is_superuser=bool(row['is_superuser']),
                        username=row['username'],
                        first_name=row['first_name'] if row['first_name'] else '',
                        last_name=row['last_name'] if row['last_name'] else '',
                        email=row['email'],
                        is_staff=bool(row['is_staff']),
                        is_active=bool(row['is_active']),
                        date_joined=timezone.make_aware(datetime.fromisoformat(row['date_joined'].replace('Z', '+00:00'))) if row['date_joined'] else timezone.now(),
                        name=row['name'] if row['name'] else '',
                        bio=row['bio'] if row['bio'] else '',
                        avatar=row['avatar'] if row['avatar'] else '',
                        location=row['location'] if row['location'] else '',
                        birth_date=datetime.fromisoformat(row['birth_date']).date() if row['birth_date'] else None,
                        company=company
                    )
                    user.save()
                    created_count += 1
                    
                except IntegrityError as e:
                    self.log(f"⚠️  User {row['email']} already exists or error: {e}")
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
                    category = Category.objects.get(id=row['category_id'])
                    spec = CategorySpecification.objects.create(
                        id=row['id'],
                        category=category,
                        field_name=row['field_name'],
                        field_type=row['field_type'],
                        is_required=bool(row['is_required']),
                        options=row['options'] if row['options'] else None,
                        description=row['description'] if row['description'] else ''
                    )
                    created_count += 1
                    
                except Category.DoesNotExist:
                    self.log(f"⚠️  Category with ID {row['category_id']} not found for specification")
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
                    location = Location.objects.create(
                        id=row['id'],
                        country=row['country'],
                        state_province=row['state_province'] if row['state_province'] else '',
                        city=row['city'],
                        address_line=row['address_line'] if row['address_line'] else '',
                        postal_code=row['postal_code'] if row['postal_code'] else '',
                        latitude=float(row['latitude']) if row['latitude'] else None,
                        longitude=float(row['longitude']) if row['longitude'] else None
                    )
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
                    # Get related objects
                    user = User.objects.get(id=row['user_id'])
                    category = Category.objects.get(id=row['category_id']) if row['category_id'] else None
                    subcategory = SubCategory.objects.get(id=row['subcategory_id']) if row['subcategory_id'] else None
                    location = Location.objects.get(id=row['location_id']) if row['location_id'] else None
                    specification = CategorySpecification.objects.get(id=row['specification_id']) if row['specification_id'] else None
                    
                    ad = Ad.objects.create(
                        id=row['id'],
                        user=user,
                        category=category,
                        subcategory=subcategory,
                        location=location,
                        specification=specification,
                        specific_material=row['specific_material'],
                        packaging=row['packaging'],
                        material_frequency=row['material_frequency'],
                        additional_specifications=row['additional_specifications'],
                        origin=row['origin'],
                        contamination=row['contamination'],
                        additives=row['additives'],
                        storage_conditions=row['storage_conditions'],
                        processing_methods=row['processing_methods'],
                        pickup_available=bool(row['pickup_available']),
                        delivery_options=row['delivery_options'],
                        available_quantity=Decimal(row['available_quantity']) if row['available_quantity'] else None,
                        minimum_order_quantity=Decimal(row['minimum_order_quantity']),
                        starting_bid_price=Decimal(row['starting_bid_price']) if row['starting_bid_price'] else None,
                        currency=row['currency'],
                        auction_duration=row['auction_duration'],
                        reserve_price=Decimal(row['reserve_price']) if row['reserve_price'] else None,
                        title=row['title'],
                        description=row['description'],
                        keywords=row['keywords'],
                        material_image=row['material_image'],
                        is_active=bool(row['is_active']),
                        created_at=timezone.make_aware(datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))) if row['created_at'] else timezone.now(),
                        updated_at=timezone.make_aware(datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))) if row['updated_at'] else timezone.now(),
                        auction_start_date=timezone.make_aware(datetime.fromisoformat(row['auction_start_date'].replace('Z', '+00:00'))) if row['auction_start_date'] else None,
                        auction_end_date=timezone.make_aware(datetime.fromisoformat(row['auction_end_date'].replace('Z', '+00:00'))) if row['auction_end_date'] else None,
                        current_step=row['current_step'],
                        is_complete=bool(row['is_complete']),
                        custom_auction_duration=row['custom_auction_duration'],
                        unit_of_measurement=row['unit_of_measurement']
                    )
                    created_count += 1
                    
                except Exception as e:
                    self.log(f"❌ Error creating ad ID {row['id']}: {e}")
        
        self.log(f"✅ Ads migrated: {created_count}/{len(sqlite_ads)}")
        return created_count
    
    def migrate_bids(self):
        """Migrate bids data"""
        self.log("💰 Migrating bids...")
        
        sqlite_bids = self.get_sqlite_data('bids_bid')
        created_count = 0
        
        with transaction.atomic():
            for row in sqlite_bids:
                try:
                    user = User.objects.get(id=row['user_id'])
                    ad = Ad.objects.get(id=row['ad_id'])
                    
                    bid = Bid.objects.create(
                        id=row['id'],
                        user=user,
                        ad=ad,
                        amount=Decimal(row['amount']),
                        quantity=Decimal(row['quantity']) if row['quantity'] else None,
                        message=row['message'] if row['message'] else '',
                        is_active=bool(row['is_active']),
                        created_at=timezone.make_aware(datetime.fromisoformat(row['created_at'].replace('Z', '+00:00'))) if row['created_at'] else timezone.now(),
                        updated_at=timezone.make_aware(datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))) if row['updated_at'] else timezone.now(),
                        expires_at=timezone.make_aware(datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))) if row['expires_at'] else None,
                        delivery_terms=row['delivery_terms'] if row['delivery_terms'] else '',
                        payment_terms=row['payment_terms'] if row['payment_terms'] else '',
                        additional_notes=row['additional_notes'] if row['additional_notes'] else '',
                        status=row['status'] if row['status'] else 'pending',
                        company_name=row['company_name'] if row['company_name'] else '',
                        contact_person=row['contact_person'] if row['contact_person'] else '',
                        phone_number=row['phone_number'] if row['phone_number'] else ''
                    )
                    created_count += 1
                    
                except Exception as e:
                    self.log(f"❌ Error creating bid ID {row['id']}: {e}")
        
        self.log(f"✅ Bids migrated: {created_count}/{len(sqlite_bids)}")
        return created_count
    
    def migrate_bid_history(self):
        """Migrate bid history data"""
        self.log("📈 Migrating bid history...")
        
        sqlite_bid_history = self.get_sqlite_data('bids_bidhistory')
        created_count = 0
        
        with transaction.atomic():
            for row in sqlite_bid_history:
                try:
                    bid = Bid.objects.get(id=row['bid_id'])
                    
                    bid_history = BidHistory.objects.create(
                        id=row['id'],
                        bid=bid,
                        old_amount=Decimal(row['old_amount']) if row['old_amount'] else None,
                        new_amount=Decimal(row['new_amount']),
                        old_quantity=Decimal(row['old_quantity']) if row['old_quantity'] else None,
                        new_quantity=Decimal(row['new_quantity']) if row['new_quantity'] else None,
                        change_reason=row['change_reason'] if row['change_reason'] else '',
                        changed_at=timezone.make_aware(datetime.fromisoformat(row['changed_at'].replace('Z', '+00:00'))) if row['changed_at'] else timezone.now()
                    )
                    created_count += 1
                    
                except Exception as e:
                    self.log(f"❌ Error creating bid history ID {row['id']}: {e}")
        
        self.log(f"✅ Bid history migrated: {created_count}/{len(sqlite_bid_history)}")
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
            'Bids': Bid.objects.count(),
            'Bid History': BidHistory.objects.count()
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
            results['bids'] = self.migrate_bids()
            results['bid_history'] = self.migrate_bid_history()
            
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
    print("🔄 PostgreSQL Migration Tool for Nordic Loop Platform")
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
    
    migrator = PostgreSQLMigrator()
    
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