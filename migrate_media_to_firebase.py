#!/usr/bin/env python3
"""
Media to Firebase Migration Script
Migrates existing local media files to Firebase Storage while preserving names
"""

import os
import django
from pathlib import Path
import mimetypes
from urllib.parse import unquote

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import sys
sys.path.append(str(BASE_DIR))

django.setup()

from base.services.firebase_service import firebase_storage_service
from django.conf import settings
from ads.models import Ad
from django.core.files.uploadedfile import SimpleUploadedFile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MediaToFirebaseMigrator:
    """
    Migrates local media files to Firebase Storage
    """
    
    def __init__(self):
        self.media_root = Path(settings.MEDIA_ROOT)
        self.migrated_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.updated_ads = 0
        
    def get_image_files(self):
        """Get all image files from media directory"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        image_files = []
        
        for root, dirs, files in os.walk(self.media_root):
            for file in files:
                if Path(file).suffix.lower() in image_extensions:
                    full_path = Path(root) / file
                    relative_path = full_path.relative_to(self.media_root)
                    image_files.append({
                        'full_path': full_path,
                        'relative_path': relative_path,
                        'filename': file
                    })
        
        return image_files
    
    def upload_to_firebase_with_original_name(self, file_info):
        """
        Upload file to Firebase preserving the original path structure
        """
        try:
            full_path = file_info['full_path']
            relative_path = file_info['relative_path']
            
            # Read the file
            with open(full_path, 'rb') as f:
                file_content = f.read()
            
            # Get content type
            content_type, _ = mimetypes.guess_type(str(full_path))
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Create a file-like object
            from io import BytesIO
            file_obj = BytesIO(file_content)
            file_obj.name = file_info['filename']
            file_obj.content_type = content_type
            
            # Create blob path preserving the original structure
            blob_path = str(relative_path).replace('\\', '/')
            
            # Upload directly to Firebase with preserved path
            blob = firebase_storage_service.bucket.blob(blob_path)
            blob.upload_from_file(file_obj, content_type=content_type)
            blob.make_public()
            
            firebase_url = blob.public_url
            
            logger.info(f"✅ Uploaded: {relative_path} -> {firebase_url}")
            return True, firebase_url, str(relative_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {relative_path}: {str(e)}")
            return False, None, str(relative_path)
    
    def update_database_records(self, local_path, firebase_url):
        """
        Update database records that reference the local file path
        """
        try:
            # Find ads that use this image path
            ads_updated = 0
            
            # Check for exact matches
            ads = Ad.objects.filter(material_image=local_path)
            for ad in ads:
                ad.material_image = firebase_url
                ad.save(update_fields=['material_image'])
                ads_updated += 1
                logger.info(f"📝 Updated Ad #{ad.id}: {local_path} -> {firebase_url}")
            
            # Check for matches with MEDIA_URL prefix
            media_url_path = settings.MEDIA_URL + local_path
            ads = Ad.objects.filter(material_image=media_url_path)
            for ad in ads:
                ad.material_image = firebase_url
                ad.save(update_fields=['material_image'])
                ads_updated += 1
                logger.info(f"📝 Updated Ad #{ad.id}: {media_url_path} -> {firebase_url}")
            
            # Check for matches without media/ prefix
            if local_path.startswith('material_images/'):
                short_path = local_path.replace('material_images/', '')
                ads = Ad.objects.filter(material_image__endswith=short_path)
                for ad in ads:
                    ad.material_image = firebase_url
                    ad.save(update_fields=['material_image'])
                    ads_updated += 1
                    logger.info(f"📝 Updated Ad #{ad.id}: {ad.material_image} -> {firebase_url}")
            
            return ads_updated
            
        except Exception as e:
            logger.error(f"❌ Failed to update database records for {local_path}: {str(e)}")
            return 0
    
    def migrate_all_files(self, dry_run=False):
        """
        Migrate all image files to Firebase
        """
        print("🔄 MEDIA TO FIREBASE MIGRATION")
        print("=" * 50)
        
        # Get all image files
        image_files = self.get_image_files()
        total_files = len(image_files)
        
        print(f"📊 Found {total_files} image files to migrate")
        print()
        
        if dry_run:
            print("🧪 DRY RUN MODE - No actual changes will be made")
            print()
        
        if total_files == 0:
            print("ℹ️  No image files found to migrate")
            return
        
        # Process each file
        for i, file_info in enumerate(image_files, 1):
            relative_path = file_info['relative_path']
            print(f"[{i}/{total_files}] Processing: {relative_path}")
            
            if dry_run:
                print(f"    Would upload: {relative_path}")
                continue
            
            # Upload to Firebase
            success, firebase_url, path = self.upload_to_firebase_with_original_name(file_info)
            
            if success:
                self.migrated_count += 1
                
                # Update database records
                updated_count = self.update_database_records(path, firebase_url)
                self.updated_ads += updated_count
                
                if updated_count > 0:
                    print(f"    ✅ Uploaded and updated {updated_count} database record(s)")
                else:
                    print(f"    ✅ Uploaded (no database records found)")
            else:
                self.failed_count += 1
                print(f"    ❌ Failed to upload")
            
            print()
    
    def verify_migration(self):
        """
        Verify that migration was successful
        """
        print("🔍 MIGRATION VERIFICATION")
        print("=" * 30)
        
        # Check ads with Firebase URLs
        firebase_ads = Ad.objects.filter(material_image__startswith='https://storage.googleapis.com/')
        local_ads = Ad.objects.filter(material_image__startswith='material_images/').exclude(material_image__startswith='https://')
        
        print(f"📊 Database Status:")
        print(f"   Ads with Firebase URLs: {firebase_ads.count()}")
        print(f"   Ads with local paths: {local_ads.count()}")
        
        if local_ads.exists():
            print(f"\n⚠️  Ads still using local paths:")
            for ad in local_ads[:5]:  # Show first 5
                print(f"   Ad #{ad.id}: {ad.material_image}")
        
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
        """
        Print migration summary
        """
        print("📊 MIGRATION SUMMARY")
        print("=" * 25)
        print(f"✅ Successfully migrated: {self.migrated_count} files")
        print(f"❌ Failed migrations: {self.failed_count} files")
        print(f"⏭️  Skipped: {self.skipped_count} files")
        print(f"📝 Database records updated: {self.updated_ads}")
        print()
        
        if self.failed_count == 0:
            print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        else:
            print(f"⚠️  Migration completed with {self.failed_count} failures")


def main():
    """
    Main migration function
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate media files to Firebase Storage')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no actual changes)')
    parser.add_argument('--verify-only', action='store_true', help='Only run verification, no migration')
    
    args = parser.parse_args()
    
    migrator = MediaToFirebaseMigrator()
    
    if args.verify_only:
        migrator.verify_migration()
        return
    
    try:
        # Test Firebase connection first
        print("🔌 Testing Firebase connection...")
        stats = firebase_storage_service.get_storage_stats()
        print(f"✅ Connected to Firebase Storage")
        print(f"   Current files: {stats.get('total_files', 0)}")
        print()
        
        # Run migration
        migrator.migrate_all_files(dry_run=args.dry_run)
        
        if not args.dry_run:
            # Print summary
            migrator.print_summary()
            
            # Run verification
            migrator.verify_migration()
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 