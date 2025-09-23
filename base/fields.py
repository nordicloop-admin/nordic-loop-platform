from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from base.services.hybrid_storage_service import hybrid_storage_service
import logging

logger = logging.getLogger(__name__)


class FirebaseImageField(models.URLField):
    """
    Custom Django field for storing image URLs with Firebase/Local hybrid storage.
    Tries Firebase first, falls back to local storage if Firebase fails.
    Maintains URL compatibility by using BACKEND_URL for local images.
    """
    
    description = "A field for storing image URLs with Firebase/Local hybrid storage"
    
    def __init__(self, folder="images", max_length=500, **kwargs):
        self.folder = folder
        kwargs['max_length'] = max_length
        super().__init__(**kwargs)
    
    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.folder != "images":
            kwargs['folder'] = self.folder
        return name, path, args, kwargs
    
    def pre_save(self, model_instance, add):
        """
        Handle file upload before saving to database
        """
        file = getattr(model_instance, self.attname)
        
        # If file is a Django uploaded file, upload it using hybrid storage
        if isinstance(file, (InMemoryUploadedFile, TemporaryUploadedFile)):
            try:
                # Get user ID if available
                user_id = getattr(model_instance, 'user_id', None) or getattr(model_instance, 'user', {}).get('id', None)
                
                # Upload using hybrid storage (Firebase first, local fallback)
                success, message, image_url = hybrid_storage_service.upload_image(
                    file, 
                    folder=self.folder,
                    user_id=user_id
                )
                
                if success and image_url:
                    # Set the image URL as the field value
                    setattr(model_instance, self.attname, image_url)
                    return image_url
                else:
                    logger.error(f"Failed to upload image: {message}")
                    raise ValidationError(f"Image upload failed: {message}")
                    
            except Exception as e:
                logger.error(f"Error uploading image: {str(e)}")
                raise ValidationError(f"Image upload error: {str(e)}")
        
        # If it's already a URL (string), return as is
        return super().pre_save(model_instance, add)
    
    def validate(self, value, model_instance):
        """
        Validate the field value
        """
        # Allow Django uploaded files during upload process
        if isinstance(value, (InMemoryUploadedFile, TemporaryUploadedFile)):
            # Validate file type
            if not value.content_type.startswith('image/'):
                raise ValidationError("Only image files are allowed.")
            
            # Validate file size (10MB limit)
            if value.size > 10 * 1024 * 1024:
                raise ValidationError("Image file too large. Maximum size is 10MB.")
            
            return
        
        # Otherwise, validate as URL
        super().validate(value, model_instance)
    
    def contribute_to_class(self, cls, name, **kwargs):
        """
        Add field to model class
        """
        super().contribute_to_class(cls, name, **kwargs)
        
        # Add helper methods to the model
        def get_image_url(instance):
            """Get the image URL"""
            return getattr(instance, name)
        
        def delete_image(instance):
            """Delete the image from storage (Firebase or local)"""
            image_url = getattr(instance, name)
            if image_url:
                success, message = hybrid_storage_service.delete_image(image_url)
                if success:
                    setattr(instance, name, None)
                    instance.save(update_fields=[name])
                return success, message
            return True, "No image to delete"
        
        def update_image(instance, new_image_file):
            """Update the image in storage (Firebase or local)"""
            old_url = getattr(instance, name)
            user_id = getattr(instance, 'user_id', None) or getattr(instance, 'user', {}).get('id', None)
            
            success, message, new_url = hybrid_storage_service.update_image(
                old_url, 
                new_image_file, 
                folder=self.folder,
                user_id=user_id
            )
            
            if success and new_url:
                setattr(instance, name, new_url)
                instance.save(update_fields=[name])
            
            return success, message, new_url
        
        def get_storage_type(instance):
            """Get the storage type for this image (firebase/local/unknown)"""
            image_url = getattr(instance, name)
            if image_url:
                return hybrid_storage_service.get_storage_type(image_url)
            return None
        
        # Add methods to model class
        setattr(cls, f'get_{name}_url', get_image_url)
        setattr(cls, f'delete_{name}', delete_image)
        setattr(cls, f'update_{name}', update_image)
        setattr(cls, f'get_{name}_storage_type', get_storage_type)
    
    def formfield(self, **kwargs):
        """
        Return appropriate form field
        """
        from django import forms
        defaults = {'widget': forms.FileInput(attrs={'accept': 'image/*'})}
        defaults.update(kwargs)
        return super().formfield(**defaults) 