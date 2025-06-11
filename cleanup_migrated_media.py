#!/usr/bin/env python3
"""
Cleanup Script for Migrated Media Files
Safely removes local media files that have been successfully migrated to Firebase
"""

import os
import shutil
from pathlib import Path

def cleanup_migrated_media():
    """
    Optional cleanup of local media files after successful Firebase migration
    """
    print("🧹 MEDIA CLEANUP SCRIPT")
    print("=" * 30)
    print("⚠️  This will remove all local media files that have been migrated to Firebase.")
    print("📋 Before running this:")
    print("   1. Verify all images are working in your app")
    print("   2. Make sure Firebase URLs are loading correctly") 
    print("   3. Consider keeping a backup of media/ folder")
    print()
    
    media_path = Path("media/material_images")
    
    if not media_path.exists():
        print("❌ Media directory not found")
        return
    
    # Count files
    image_files = list(media_path.glob("*"))
    file_count = len([f for f in image_files if f.is_file()])
    
    print(f"📁 Found {file_count} files in {media_path}")
    
    response = input("\n⚠️  Are you sure you want to delete these local files? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Cleanup cancelled")
        return
    
    try:
        # Move to backup folder first (safer approach)
        backup_path = Path("media_backup_" + str(int(time.time())))
        shutil.move(str(media_path), str(backup_path))
        
        print(f"✅ Local media files moved to: {backup_path}")
        print("💡 You can delete this backup folder after confirming everything works")
        print("   Command: rm -rf " + str(backup_path))
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    import time
    cleanup_migrated_media() 