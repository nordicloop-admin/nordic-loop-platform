#!/usr/bin/env python3
"""
Test Firebase Credentials Configuration
Verifies that Firebase authentication works across different environments
"""

import os
import django
import json
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import sys
sys.path.append(str(BASE_DIR))

django.setup()

from base.services.firebase_service import firebase_storage_service
from django.conf import settings

def test_firebase_credentials():
    """Test Firebase credentials configuration"""
    print("🔥 FIREBASE CREDENTIALS TEST")
    print("=" * 40)
    
    # Check environment
    print(f"🌍 Environment: {'Production' if not settings.DEBUG else 'Development'}")
    print(f"📦 Firebase Bucket: {settings.FIREBASE_STORAGE_BUCKET}")
    print()
    
    # Check credential sources
    print("🔑 Credential Sources:")
    
    # Development credentials
    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
    if cred_path:
        exists = os.path.exists(cred_path)
        print(f"   FIREBASE_CREDENTIALS_PATH: {cred_path}")
        print(f"   File exists: {'✅' if exists else '❌'}")
    else:
        print(f"   FIREBASE_CREDENTIALS_PATH: ❌ Not set")
    
    # Production credentials (JSON string)
    google_creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if google_creds_json:
        try:
            # Validate JSON
            json.loads(google_creds_json)
            print(f"   GOOGLE_APPLICATION_CREDENTIALS_JSON: ✅ Valid JSON ({len(google_creds_json)} chars)")
        except json.JSONDecodeError:
            print(f"   GOOGLE_APPLICATION_CREDENTIALS_JSON: ❌ Invalid JSON")
    else:
        print(f"   GOOGLE_APPLICATION_CREDENTIALS_JSON: ❌ Not set")
    
    # Standard Google credentials
    google_creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if google_creds_path:
        exists = os.path.exists(google_creds_path)
        print(f"   GOOGLE_APPLICATION_CREDENTIALS: {google_creds_path}")
        print(f"   File exists: {'✅' if exists else '❌'}")
    else:
        print(f"   GOOGLE_APPLICATION_CREDENTIALS: ❌ Not set")
    
    print()
    
    # Test Firebase connection
    print("🧪 Testing Firebase Connection:")
    
    try:
        # Test bucket access
        bucket = firebase_storage_service.bucket
        print(f"   Bucket name: {bucket.name}")
        
        # Test storage stats
        stats = firebase_storage_service.get_storage_stats()
        print(f"   Total files: {stats.get('total_files', 0)}")
        print(f"   Storage used: {stats.get('total_size_mb', 0)} MB")
        
        print("   Status: ✅ Connection successful!")
        
        # Test upload capability (small test)
        print("\n🔄 Testing Upload Capability:")
        test_blob = bucket.blob('test_connection.txt')
        test_blob.upload_from_string('Test connection successful', content_type='text/plain')
        test_blob.make_public()
        
        print(f"   Test upload: ✅ Success")
        print(f"   Test URL: {test_blob.public_url}")
        
        # Clean up test file
        test_blob.delete()
        print(f"   Cleanup: ✅ Test file removed")
        
        return True
        
    except Exception as e:
        print(f"   Status: ❌ Connection failed")
        print(f"   Error: {str(e)}")
        return False

def check_migration_readiness():
    """Check if environment is ready for production migration"""
    print("\n📋 Migration Readiness Check:")
    print("=" * 30)
    
    # Database check
    db_engine = settings.DATABASES['default']['ENGINE']
    is_postgres = 'postgresql' in db_engine
    print(f"Database: {'✅ PostgreSQL' if is_postgres else '⚠️  SQLite'}")
    
    # Firebase check
    try:
        firebase_storage_service.bucket
        firebase_ok = True
        print(f"Firebase: ✅ Connected")
    except:
        firebase_ok = False
        print(f"Firebase: ❌ Connection failed")
    
    # Environment check
    is_production = not settings.DEBUG
    print(f"Environment: {'✅ Production' if is_production else '⚠️  Development'}")
    
    # Overall readiness
    ready = is_postgres and firebase_ok
    
    print(f"\n🎯 Migration Ready: {'✅ YES' if ready else '❌ NO'}")
    
    if not ready:
        print("\n📝 TODO:")
        if not is_postgres:
            print("   - Switch to PostgreSQL database")
        if not firebase_ok:
            print("   - Fix Firebase connection")
    
    return ready

def main():
    """Main test function"""
    try:
        # Test credentials
        credentials_ok = test_firebase_credentials()
        
        # Check migration readiness
        migration_ready = check_migration_readiness()
        
        print("\n" + "=" * 50)
        print("📊 SUMMARY:")
        print(f"   Firebase Credentials: {'✅ Working' if credentials_ok else '❌ Failed'}")
        print(f"   Migration Ready: {'✅ Yes' if migration_ready else '❌ No'}")
        
        if credentials_ok and migration_ready:
            print("\n🎉 All systems ready for production Firebase migration!")
            print("   Run: python migrate_production_to_firebase.py --dry-run")
        else:
            print("\n⚠️  Please fix the issues above before running migration")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 