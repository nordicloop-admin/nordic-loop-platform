import os
import uuid
import tempfile
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
import firebase_admin
from firebase_admin import credentials, storage
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
import logging

logger = logging.getLogger(__name__)


class FirebaseStorageService:
    """
    Firebase Storage service for handling image uploads and management.
    Provides secure, scalable cloud storage for user-uploaded images.
    """
    
    def __init__(self):
        self._bucket = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK if not already initialized"""
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
            logger.info("Firebase already initialized")
        except ValueError:
            # Initialize Firebase
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            
            if cred_path and os.path.exists(cred_path):
                # Use service account file
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
                logger.info("Firebase initialized with service account file")
            else:
                # Use environment variables (for production)
                firebase_admin.initialize_app(options={
                    'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                })
                logger.info("Firebase initialized with environment variables")
    
    @property
    def bucket(self):
        """Get Firebase Storage bucket instance"""
        if not self._bucket:
            self._bucket = storage.bucket()
        return self._bucket
    
    def upload_image(self, 
                    image_file: Any, 
                    folder: str = "material_images",
                    user_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Upload image to Firebase Storage
        
        Args:
            image_file: Django uploaded file or file-like object
            folder: Storage folder/path (default: "material_images")
            user_id: User ID for organizing files (optional)
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, download_url)
        """
        try:
            # Generate unique filename
            filename = self._generate_filename(image_file.name, user_id)
            
            # Create full path
            if user_id:
                blob_path = f"{folder}/user_{user_id}/{filename}"
            else:
                blob_path = f"{folder}/{filename}"
            
            # Create blob reference
            blob = self.bucket.blob(blob_path)
            
            # Upload file
            if isinstance(image_file, (InMemoryUploadedFile, TemporaryUploadedFile)):
                # Django uploaded file
                image_file.seek(0)  # Reset file pointer
                blob.upload_from_file(image_file, content_type=image_file.content_type)
            else:
                # Handle other file types
                blob.upload_from_file(image_file)
            
            # Make blob publicly readable
            blob.make_public()
            
            # Get download URL
            download_url = blob.public_url
            
            logger.info(f"Successfully uploaded image to Firebase: {blob_path}")
            return True, "Image uploaded successfully", download_url
            
        except Exception as e:
            logger.error(f"Failed to upload image to Firebase: {str(e)}")
            return False, f"Upload failed: {str(e)}", None
    
    def delete_image(self, image_url: str) -> Tuple[bool, str]:
        """
        Delete image from Firebase Storage
        
        Args:
            image_url: Firebase Storage URL or blob path
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Extract blob path from URL
            blob_path = self._extract_blob_path(image_url)
            if not blob_path:
                return False, "Invalid image URL"
            
            # Get blob reference
            blob = self.bucket.blob(blob_path)
            
            # Delete the blob
            blob.delete()
            
            logger.info(f"Successfully deleted image from Firebase: {blob_path}")
            return True, "Image deleted successfully"
            
        except Exception as e:
            logger.error(f"Failed to delete image from Firebase: {str(e)}")
            return False, f"Delete failed: {str(e)}"
    
    def get_image_metadata(self, image_url: str) -> Optional[Dict[str, Any]]:
        """
        Get image metadata from Firebase Storage
        
        Args:
            image_url: Firebase Storage URL or blob path
            
        Returns:
            Optional[Dict]: Image metadata or None if failed
        """
        try:
            blob_path = self._extract_blob_path(image_url)
            if not blob_path:
                return None
            
            blob = self.bucket.blob(blob_path)
            blob.reload()
            
            return {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created,
                'updated': blob.updated,
                'public_url': blob.public_url
            }
            
        except Exception as e:
            logger.error(f"Failed to get image metadata: {str(e)}")
            return None
    
    def update_image(self, 
                    old_image_url: str, 
                    new_image_file: Any,
                    folder: str = "material_images",
                    user_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Replace existing image with new one
        
        Args:
            old_image_url: URL of existing image to replace
            new_image_file: New image file to upload
            folder: Storage folder/path
            user_id: User ID for organizing files
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, new_download_url)
        """
        try:
            # Upload new image first
            success, message, new_url = self.upload_image(new_image_file, folder, user_id)
            
            if not success:
                return False, f"Failed to upload new image: {message}", None
            
            # Delete old image if upload was successful
            if old_image_url:
                delete_success, delete_message = self.delete_image(old_image_url)
                if not delete_success:
                    logger.warning(f"Failed to delete old image: {delete_message}")
            
            return True, "Image updated successfully", new_url
            
        except Exception as e:
            logger.error(f"Failed to update image: {str(e)}")
            return False, f"Update failed: {str(e)}", None
    
    def _generate_filename(self, original_filename: str, user_id: Optional[int] = None) -> str:
        """Generate unique filename for uploaded image"""
        # Get file extension
        name, ext = os.path.splitext(original_filename)
        if not ext:
            ext = '.jpg'  # Default extension
        
        # Generate unique identifier
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create filename
        if user_id:
            filename = f"{name}_{user_id}_{timestamp}_{unique_id}{ext}"
        else:
            filename = f"{name}_{timestamp}_{unique_id}{ext}"
        
        # Clean filename (remove special characters)
        filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        return filename
    
    def _extract_blob_path(self, image_url: str) -> Optional[str]:
        """Extract blob path from Firebase Storage URL"""
        try:
            if not image_url:
                return None
            
            # If it's already a blob path, return as is
            if not image_url.startswith('http'):
                return image_url
            
            # Extract from Firebase Storage URL
            # Example: https://storage.googleapis.com/bucket-name/path/to/file.jpg
            if 'storage.googleapis.com' in image_url:
                parts = image_url.split('/')
                if len(parts) >= 5:
                    return '/'.join(parts[4:])  # Remove protocol, domain, and bucket
            
            # Extract from Firebase public URL
            # Example: https://firebasestorage.googleapis.com/v0/b/bucket/o/path%2Ffile.jpg?alt=media
            if 'firebasestorage.googleapis.com' in image_url:
                from urllib.parse import unquote
                if '/o/' in image_url:
                    path_part = image_url.split('/o/')[1].split('?')[0]
                    return unquote(path_part)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract blob path from URL: {str(e)}")
            return None
    
    def list_user_images(self, user_id: int, folder: str = "material_images") -> List[Dict[str, Any]]:
        """
        List all images for a specific user
        
        Args:
            user_id: User ID
            folder: Storage folder to search in
            
        Returns:
            List[Dict]: List of image metadata
        """
        try:
            prefix = f"{folder}/user_{user_id}/"
            blobs = self.bucket.list_blobs(prefix=prefix)
            
            images = []
            for blob in blobs:
                images.append({
                    'name': blob.name,
                    'size': blob.size,
                    'content_type': blob.content_type,
                    'public_url': blob.public_url,
                    'created': blob.time_created,
                    'updated': blob.updated
                })
            
            return images
            
        except Exception as e:
            logger.error(f"Failed to list user images: {str(e)}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage usage statistics"""
        try:
            all_blobs = list(self.bucket.list_blobs())
            
            total_size = sum(blob.size or 0 for blob in all_blobs)
            total_files = len(all_blobs)
            
            # Group by content type
            content_types = {}
            for blob in all_blobs:
                content_type = blob.content_type or 'unknown'
                content_types[content_type] = content_types.get(content_type, 0) + 1
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'content_types': content_types
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {str(e)}")
            return {}


# Singleton instance
firebase_storage_service = FirebaseStorageService() 