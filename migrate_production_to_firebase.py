#!/usr/bin/env python3
"""
Production Firebase Migration Script
Updates PostgreSQL database to use Firebase URLs for existing images
"""

import os
import django
from pathlib import Path
import mimetypes
import argparse

# Setup Django for production
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import sys
sys.path.append(str(BASE_DIR))

django.setup()

from base.services.firebase_service import firebase_storage_service
from django.conf import settings
from ads.models import Ad
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionFirebaseMigrator:
    """
    Migrates production database records from local paths to Firebase URLs
    """
    
    def __init__(self):
        self.updated_count = 0
        self.failed_count = 0
        self.firebase_base_url = f"https://storage.googleapis.com/{firebase_storage_service.bucket.name}"
        
    def check_environment(self):
        """Check if we're running in the right environment"""
        db_engine = settings.DATABASES['default']['ENGINE']
        
        print("🔍 ENVIRONMENT CHECK")
        print("=" * 30)
        print(f"Database Engine: {db_engine}")
        print(f"DEBUG Mode: {settings.DEBUG}")
        print(f"Firebase Bucket: {firebase_storage_service.bucket.name}")
        
        # Check Firebase credentials configuration
        print(f"\n🔑 Firebase Credentials:")
        cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        google_creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        google_creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if cred_path:
            print(f"   FIREBASE_CREDENTIALS_PATH: {cred_path}")
            print(f"   File exists: {os.path.exists(cred_path) if cred_path else False}")
        
        if google_creds_json:
            print(f"   GOOGLE_APPLICATION_CREDENTIALS_JSON: ✅ Set (length: {len(google_creds_json)} chars)")
        else:
            print(f"   GOOGLE_APPLICATION_CREDENTIALS_JSON: ❌ Not set")
        
        if google_creds_path:
            print(f"   GOOGLE_APPLICATION_CREDENTIALS: {google_creds_path}")
            print(f"   File exists: {os.path.exists(google_creds_path) if google_creds_path else False}")
        else:
            print(f"   GOOGLE_APPLICATION_CREDENTIALS: ❌ Not set")
        
        print()
        
        if 'postgresql' not in db_engine:
            print("⚠️  Warning: This script is designed for PostgreSQL production database")
        
        # Verify we have some form of credentials
        if not any([
            cred_path and os.path.exists(cred_path),
            google_creds_json,
            google_creds_path and os.path.exists(google_creds_path)
        ]):
            print("❌ No Firebase credentials found!")
            print("   For development: Set FIREBASE_CREDENTIALS_PATH in .env")
            print("   For production: Set GOOGLE_APPLICATION_CREDENTIALS_JSON with JSON content")
            return False
            
        return True
    
    def find_ads_with_local_paths(self):
        """Find all ads currently using local image paths"""
        local_path_ads = Ad.objects.filter(
            material_image__startswith='material_images/'
        ).exclude(
            material_image__startswith='https://'
        )
        
        return local_path_ads
    
    def convert_local_path_to_firebase_url(self, local_path):
        """Convert local path to Firebase URL"""
        # Remove any leading slashes or media prefix
        clean_path = local_path.strip('/')
        if clean_path.startswith('media/'):
            clean_path = clean_path[6:]  # Remove 'media/' prefix
        
        # Construct Firebase URL
        firebase_url = f"{self.firebase_base_url}/{clean_path}"
        
        return firebase_url
    
    def verify_firebase_image_exists(self, firebase_path):
        """Check if image exists in Firebase Storage"""
        try:
            # Extract path from full Firebase URL
            if firebase_path.startswith('https://'):
                # Extract path after bucket name
                path_parts = firebase_path.split(f"{firebase_storage_service.bucket.name}/")
                if len(path_parts) == 2:
                    blob_path = path_parts[1]
                else:
                    return False
            else:
                blob_path = firebase_path
            
            blob = firebase_storage_service.bucket.blob(blob_path)
            return blob.exists()
            
        except Exception as e:
            logger.error(f"Error checking Firebase image {firebase_path}: {str(e)}")
            return False
    
    def update_ad_image_url(self, ad, new_firebase_url, dry_run=False):
        """Update ad with new Firebase URL"""
        try:
            old_path = ad.material_image
            
            if dry_run:
                print(f"    Would update Ad #{ad.id}: {old_path} -> {new_firebase_url}")
                return True
            
            ad.material_image = new_firebase_url
            ad.save(update_fields=['material_image'])
            
            logger.info(f"✅ Updated Ad #{ad.id}: {old_path} -> {new_firebase_url}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update Ad #{ad.id}: {str(e)}")
            return False
    
    def migrate_production_database(self, dry_run=False, verify_firebase=True):
        """
        Main migration function for production database
        """
        print("🔄 PRODUCTION FIREBASE URL MIGRATION")
        print("=" * 50)
        
        if dry_run:
            print("🧪 DRY RUN MODE - No actual changes will be made")
            print()
        
        # Find ads with local paths
        local_ads = self.find_ads_with_local_paths()
        total_ads = local_ads.count()
        
        print(f"📊 Found {total_ads} ads with local image paths")
        
        if total_ads == 0:
            print("✅ No ads found with local paths - migration may already be complete!")
            return
        
        print()
        
        # Process each ad
        for i, ad in enumerate(local_ads, 1):
            local_path = ad.material_image
            firebase_url = self.convert_local_path_to_firebase_url(local_path)
            
            print(f"[{i}/{total_ads}] Processing Ad #{ad.id}")
            print(f"    Local path: {local_path}")
            print(f"    Firebase URL: {firebase_url}")
            
            # Verify image exists in Firebase (optional)
            if verify_firebase and not dry_run:
                blob_path = local_path
                if not self.verify_firebase_image_exists(blob_path):
                    print(f"    ⚠️  Image not found in Firebase: {blob_path}")
                    print(f"    📤 Consider uploading this image first")
                    self.failed_count += 1
                    continue
            
            # Update the ad
            success = self.update_ad_image_url(ad, firebase_url, dry_run)
            
            if success:
                self.updated_count += 1
                print(f"    ✅ Updated successfully")
            else:
                self.failed_count += 1
                print(f"    ❌ Update failed")
            
            print()
    
    def verify_migration_status(self):
        """Check current migration status"""
        print("🔍 MIGRATION STATUS CHECK")
        print("=" * 30)
        
        # Count ads by image URL type
        firebase_ads = Ad.objects.filter(material_image__startswith='https://storage.googleapis.com/').count()
        local_ads = Ad.objects.filter(material_image__startswith='material_images/').exclude(material_image__startswith='https://').count()
        total_ads = Ad.objects.exclude(material_image__isnull=True).exclude(material_image='').count()
        
        print(f"📊 Database Status:")
        print(f"   Total ads with images: {total_ads}")
        print(f"   Ads with Firebase URLs: {firebase_ads}")
        print(f"   Ads with local paths: {local_ads}")
        print()
        
        if local_ads > 0:
            print("⚠️  Ads still using local paths:")
            local_path_ads = Ad.objects.filter(material_image__startswith='material_images/').exclude(material_image__startswith='https://')[:5]
            for ad in local_path_ads:
                print(f"   Ad #{ad.id}: {ad.material_image}")
        else:
            print("✅ All ads are using Firebase URLs!")
        
        print()
        
        # Test Firebase connectivity
        try:
            stats = firebase_storage_service.get_storage_stats()
            print(f"🔥 Firebase Storage Status:")
            print(f"   Total files: {stats.get('total_files', 0)}")
            print(f"   Storage used: {stats.get('total_size_mb', 0)} MB")
        except Exception as e:
            print(f"❌ Firebase connection error: {str(e)}")
    
    def print_summary(self):
        """Print migration summary"""
        print("📊 MIGRATION SUMMARY")
        print("=" * 25)
        print(f"✅ Successfully updated: {self.updated_count} ads")
        print(f"❌ Failed updates: {self.failed_count} ads")
        print()
        
        if self.failed_count == 0:
            print("🎉 PRODUCTION MIGRATION COMPLETED SUCCESSFULLY!")
        else:
            print(f"⚠️  Migration completed with {self.failed_count} failures")


def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description='Migrate production database to Firebase URLs')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual changes)')
    parser.add_argument('--status-only', action='store_true', help='Only check migration status')
    parser.add_argument('--skip-verification', action='store_true', help='Skip Firebase image verification')
    
    args = parser.parse_args()
    
    migrator = ProductionFirebaseMigrator()
    
    try:
        # Check environment
        migrator.check_environment()
        
        if args.status_only:
            migrator.verify_migration_status()
            return
        
        # Get user confirmation for production
        if not args.dry_run:
            print("⚠️  WARNING: This will modify your PRODUCTION database!")
            print("📋 Make sure you have:")
            print("   1. A database backup")
            print("   2. All images uploaded to Firebase")
            print("   3. Verified this works in development")
            print()
            
            confirm = input("Are you sure you want to proceed? (type 'yes' to continue): ")
            if confirm.lower() != 'yes':
                print("❌ Migration cancelled")
                return
        
        # Test Firebase connection
        print("🔌 Testing Firebase connection...")
        stats = firebase_storage_service.get_storage_stats()
        print(f"✅ Connected to Firebase Storage")
        print(f"   Current files: {stats.get('total_files', 0)}")
        print()
        
        # Run migration
        verify_firebase = not args.skip_verification
        migrator.migrate_production_database(
            dry_run=args.dry_run, 
            verify_firebase=verify_firebase
        )
        
        if not args.dry_run:
            # Print summary
            migrator.print_summary()
            
            # Verify final status
            migrator.verify_migration_status()
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 