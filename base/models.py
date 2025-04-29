from django.db import models
from django.utils import timezone
import uuid


class BaseModel(models.Model):
    """
    Base model class for all models in the application.
    
    This class provides common fields and functionality for all models.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Address(BaseModel):
    """
    Model for storing address information.
    """
    country = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    street_number = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    additional_info = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Addresses"
    
    def __str__(self):
        return f"{self.street_number}, {self.city}, {self.country}"
