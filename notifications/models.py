from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    """
    Notification model for storing user notifications
    """
    NOTIFICATION_TYPES = [
        ('feature', 'Feature'),
        ('system', 'System'),
        ('auction', 'Auction'),
        ('promotion', 'Promotion'),
        ('welcome', 'Welcome'),
    ]
    
    title = models.CharField(max_length=255)
    message = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.title} - {self.date.strftime('%Y-%m-%d %H:%M')}"
