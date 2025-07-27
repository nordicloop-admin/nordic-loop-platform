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
        ('subscription', 'Subscription'),
        ('security', 'Security'),
        ('account', 'Account'),
        ('bid', 'Bid'),
        ('payment', 'Payment'),
        ('admin', 'Admin'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    SUBSCRIPTION_TARGET_CHOICES = [
        ('all', 'All Users'),
        ('free', 'Free Plan Users'),
        ('standard', 'Standard Plan Users'),
        ('premium', 'Premium Plan Users'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    date = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='feature')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    action_url = models.URLField(blank=True, null=True, help_text="Optional URL for notification action")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata for the notification")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    subscription_target = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_TARGET_CHOICES,
        default='all',
        help_text="Target users based on their subscription plan"
    )
    
    class Meta:
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.title} - {self.date.strftime('%Y-%m-%d %H:%M')}"
