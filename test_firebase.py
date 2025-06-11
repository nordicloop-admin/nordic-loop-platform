#!/usr/bin/env python3
"""
Firebase Storage Test Script
Tests Firebase integration for Nordic Loop Platform
"""

import os
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import sys
sys.path.append(str(BASE_DIR))

django.setup()

from base.services.firebase_service import firebase_storage_service
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

def test_firebase_connectivity():
    """Test basic Firebase connectivity"""
    print("🔥 TESTING FIREBASE STORAGE INTEGRATION")
    print("=" * 50)
    
    # Check settings
    print(f"📋 Settings Check:")
    print(f"   Storage Bucket: {settings.FIREBASE_STORAGE_BUCKET}")
    print(f"   Credentials Path: {settings.FIREBASE_CREDENTIALS_PATH}")
    print()
    
    # Test connection
    print("🔌 Testing Firebase Connection...")
    try:
        stats = firebase_storage_service.get_storage_stats()
        print("✅ Firebase connection successful!")
        print(f"   Total files in storage: {stats.get('total_files', 0)}")
        print(f"   Total storage used: {stats.get('total_size_mb', 0)} MB")
        if stats.get('content_types'):
            print(f"   Content types: {stats.get('content_types')}")
        print()
        return True
    except Exception as e:
        print(f"❌ Firebase connection failed: {str(e)}")
        print()
        return False

def test_image_upload():
    """Test image upload functionality"""
    print("📤 Testing Image Upload...")
    
    # Create a simple test image (1x1 pixel PNG)
    # This is a minimal valid PNG file in base64
    import base64
    
    # 1x1 red pixel PNG
    png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
    )
    
    test_file = SimpleUploadedFile(
        name='test_image.png',
        content=png_data,
        content_type='image/png'
    )
    
    try:
        success, message, url = firebase_storage_service.upload_image(test_file, user_id=1)
        
        if success:
            print(f"✅ Image upload successful!")
            print(f"   URL: {url}")
            print(f"   Message: {message}")
            
            # Test image deletion
            print("\n🗑️  Testing Image Deletion...")
            delete_success, delete_message = firebase_storage_service.delete_image(url)
            if delete_success:
                print(f"✅ Image deletion successful!")
                print(f"   Message: {delete_message}")
            else:
                print(f"❌ Image deletion failed: {delete_message}")
            
            return True
        else:
            print(f"❌ Image upload failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Image upload error: {str(e)}")
        return False

def test_model_integration():
    """Test model integration"""
    print("\n🔗 Testing Model Integration...")
    
    try:
        from ads.models import Ad
        from users.models import User
        
        # Check if FirebaseImageField is properly set up
        field = Ad._meta.get_field('material_image')
        print(f"✅ Model field type: {type(field).__name__}")
        print(f"   Field folder: {getattr(field, 'folder', 'Not set')}")
        print(f"   Field max_length: {getattr(field, 'max_length', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model integration error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 FIREBASE INTEGRATION TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("Firebase Connectivity", test_firebase_connectivity),
        ("Image Upload & Delete", test_image_upload),
        ("Model Integration", test_model_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🔍 Running: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Firebase integration is working correctly!")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    main() 