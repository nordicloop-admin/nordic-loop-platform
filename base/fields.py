from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
from base.services.firebase_service import firebase_storage_service
import logging

logger = logging.getLogger(__name__)


class FirebaseImageField(models.URLField):
    """
    Custom Django field for storing Firebase Storage image URLs.
    Handles image uploads to Firebase Storage automatically.
    """
    
    description = "A field for storing Firebase Storage image URLs"
    
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
        
        # If file is a Django uploaded file, upload it to Firebase
        if isinstance(file, (InMemoryUploadedFile, TemporaryUploadedFile)):
            try:
                # Get user ID if available
                user_id = getattr(model_instance, 'user_id', None) or getattr(model_instance, 'user', {}).get('id', None)
                
                # Upload to Firebase
                success, message, firebase_url = firebase_storage_service.upload_image(
                    file, 
                    folder=self.folder,
                    user_id=user_id
                )
                
                if success and firebase_url:
                    # Set the Firebase URL as the field value
                    setattr(model_instance, self.attname, firebase_url)
                    return firebase_url
                else:
                    logger.error(f"Failed to upload image to Firebase: {message}")
                    raise ValidationError(f"Image upload failed: {message}")
                    
            except Exception as e:
                logger.error(f"Error uploading image to Firebase: {str(e)}")
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
            """Get the Firebase image URL"""
            return getattr(instance, name)
        
        def delete_image(instance):
            """Delete the image from Firebase Storage"""
            image_url = getattr(instance, name)
            if image_url:
                success, message = firebase_storage_service.delete_image(image_url)
                if success:
                    setattr(instance, name, None)
                    instance.save(update_fields=[name])
                return success, message
            return True, "No image to delete"
        
        def update_image(instance, new_image_file):
            """Update the image in Firebase Storage"""
            old_url = getattr(instance, name)
            user_id = getattr(instance, 'user_id', None) or getattr(instance, 'user', {}).get('id', None)
            
            success, message, new_url = firebase_storage_service.update_image(
                old_url, 
                new_image_file, 
                folder=self.folder,
                user_id=user_id
            )
            
            if success and new_url:
                setattr(instance, name, new_url)
                instance.save(update_fields=[name])
            
            return success, message, new_url
        
        # Add methods to model class
        setattr(cls, f'get_{name}_url', get_image_url)
        setattr(cls, f'delete_{name}', delete_image)
        setattr(cls, f'update_{name}', update_image)
    
    def formfield(self, **kwargs):
        """
        Return appropriate form field
        """
        from django import forms
        defaults = {'widget': forms.FileInput(attrs={'accept': 'image/*'})}
        defaults.update(kwargs)
        return super().formfield(**defaults) 