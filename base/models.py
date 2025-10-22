from django.db import models
from django.utils import timezone

class ImageMigrationRecord(models.Model):
    """Track migration from Firebase image URL to R2 URL for auditing and rollback."""
    original_firebase_url = models.URLField(max_length=500, db_index=True)
    original_local_path = models.CharField(max_length=500, blank=True, help_text="Relative path in MEDIA_ROOT for local source")
    r2_url = models.URLField(max_length=500, blank=True, null=True, db_index=True)
    object_model = models.CharField(max_length=120, help_text="Django model label e.g. ads.Ad")
    object_id = models.CharField(max_length=64, help_text="Primary key of referenced object (string for flexibility)")
    field_name = models.CharField(max_length=120, help_text="Field name storing the URL")
    status = models.CharField(max_length=32, default='pending', choices=[
        ('pending', 'Pending'),
        ('migrated', 'Migrated'),
        ('failed', 'Failed'),
        ('verified', 'Verified'),
    ])
    checksum = models.CharField(max_length=64, blank=True, help_text="Optional content hash for integrity")
    size_bytes = models.BigIntegerField(blank=True, null=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['object_model', 'field_name']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"MigrationRecord({self.object_model}:{self.object_id} {self.field_name})"
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


