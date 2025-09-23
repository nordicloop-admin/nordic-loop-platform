import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, Tuple, Any
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from base.services.firebase_service import firebase_storage_service
import logging

logger = logging.getLogger(__name__)


class HybridImageStorageService:
    """
    Hybrid image storage service that tries Firebase first, then falls back to local storage.
    Maintains URL compatibility by using BACKEND_URL + local path for local images.
    """
    
    def __init__(self):
        self.backend_url = getattr(settings, 'BACKEND_URL', 'http://127.0.0.1:8000')
        self.media_url = settings.MEDIA_URL
        self.media_root = settings.MEDIA_ROOT
        
        # Ensure media directory exists
        os.makedirs(self.media_root, exist_ok=True)
    
    def upload_image(self, 
                    image_file: Any, 
                    folder: str = "material_images",
                    user_id: Optional[int] = None,
                    force_local: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        Upload image with Firebase first, local storage as fallback.
        
        Args:
            image_file: Django uploaded file or file-like object
            folder: Storage folder/path (default: "material_images")
            user_id: User ID for organizing files (optional)
            force_local: Force local storage (for testing)
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, download_url)
        """
        if not force_local:
            # Try Firebase first
            try:
                success, message, firebase_url = firebase_storage_service.upload_image(
                    image_file, folder, user_id
                )
                
                if success and firebase_url:
                    logger.info(f"Successfully uploaded image to Firebase: {firebase_url}")
                    return True, "Image uploaded to Firebase successfully", firebase_url
                else:
                    logger.warning(f"Firebase upload failed: {message}")
            
            except Exception as e:
                logger.warning(f"Firebase upload error: {str(e)}, falling back to local storage")
        
        # Fallback to local storage
        try:
            local_url = self._upload_to_local(image_file, folder, user_id)
            logger.info(f"Successfully uploaded image to local storage: {local_url}")
            return True, "Image uploaded to local storage successfully", local_url
            
        except Exception as e:
            logger.error(f"Local storage upload failed: {str(e)}")
            return False, f"Upload failed: {str(e)}", None
    
    def _upload_to_local(self, 
                        image_file: Any, 
                        folder: str,
                        user_id: Optional[int] = None) -> str:
        """Upload image to local storage and return URL"""
        
        # Generate unique filename
        filename = self._generate_filename(image_file.name, user_id)
        
        # Create directory structure
        if user_id:
            relative_path = f"{folder}/user_{user_id}/{filename}"
        else:
            relative_path = f"{folder}/{filename}"
        
        full_dir = os.path.join(self.media_root, os.path.dirname(relative_path))
        os.makedirs(full_dir, exist_ok=True)
        
        # Save file
        full_path = os.path.join(self.media_root, relative_path)
        
        # Reset file pointer if it's an uploaded file
        if hasattr(image_file, 'seek'):
            image_file.seek(0)
        
        # Copy file to destination
        if isinstance(image_file, (InMemoryUploadedFile, TemporaryUploadedFile)):
            with open(full_path, 'wb') as dest_file:
                for chunk in image_file.chunks():
                    dest_file.write(chunk)
        else:
            # Handle file-like objects
            with open(full_path, 'wb') as dest_file:
                shutil.copyfileobj(image_file, dest_file)
        
        # Return full URL using backend URL
        local_url = f"{self.backend_url.rstrip('/')}{self.media_url}{relative_path}"
        
        return local_url
    
    def delete_image(self, image_url: str) -> Tuple[bool, str]:
        """Delete image from appropriate storage (Firebase or local)"""
        
        if self._is_firebase_url(image_url):
            # Delete from Firebase
            try:
                return firebase_storage_service.delete_image(image_url)
            except Exception as e:
                logger.error(f"Failed to delete Firebase image: {str(e)}")
                return False, f"Firebase deletion failed: {str(e)}"
        
        elif self._is_local_url(image_url):
            # Delete from local storage
            try:
                # Extract relative path from URL
                relative_path = self._extract_local_path(image_url)
                if relative_path:
                    full_path = os.path.join(self.media_root, relative_path)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        logger.info(f"Deleted local image: {full_path}")
                        return True, "Local image deleted successfully"
                    else:
                        return False, "Local image file not found"
                else:
                    return False, "Invalid local image URL"
            except Exception as e:
                logger.error(f"Failed to delete local image: {str(e)}")
                return False, f"Local deletion failed: {str(e)}"
        
        else:
            return False, "Unrecognized image URL format"
    
    def update_image(self, 
                    old_image_url: str, 
                    new_image_file: Any,
                    folder: str = "material_images",
                    user_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        """Replace existing image with new one"""
        
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
    
    def _is_firebase_url(self, url: str) -> bool:
        """Check if URL is a Firebase Storage URL"""
        if not url:
            return False
        return 'firebasestorage.googleapis.com' in url or 'storage.googleapis.com' in url
    
    def _is_local_url(self, url: str) -> bool:
        """Check if URL is a local storage URL"""
        if not url:
            return False
        return self.backend_url in url and self.media_url in url
    
    def _extract_local_path(self, url: str) -> Optional[str]:
        """Extract relative path from local storage URL"""
        try:
            if not self._is_local_url(url):
                return None
            
            # Remove backend URL and media URL to get relative path
            url_without_backend = url.replace(self.backend_url.rstrip('/'), '')
            if url_without_backend.startswith(self.media_url):
                return url_without_backend[len(self.media_url):]
            
            return None
        except Exception as e:
            logger.error(f"Failed to extract local path from URL: {str(e)}")
            return None
    
    def _generate_filename(self, original_filename: str, user_id: Optional[int] = None) -> str:
        """Generate unique filename for uploaded image"""
        # Get file extension
        name, ext = os.path.splitext(original_filename) if original_filename else ('image', '.jpg')
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
    
    def get_storage_type(self, image_url: str) -> str:
        """Determine storage type from URL"""
        if self._is_firebase_url(image_url):
            return 'firebase'
        elif self._is_local_url(image_url):
            return 'local'
        else:
            return 'unknown'


# Singleton instance
hybrid_storage_service = HybridImageStorageService()