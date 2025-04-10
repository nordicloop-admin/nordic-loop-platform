from django.db import models
from django.core.validators import MinLengthValidator
from users.models import CustomUser
from django.utils import timezone

class Company(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]
    
    # Basic company information (collected during registration)
    vat_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[MinLengthValidator(8)]
    )
    official_name = models.CharField(max_length=255)
    business_address = models.TextField()
    phone_number = models.CharField(max_length=20)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(unique=True)  # Company email for communications
    registration_date = models.DateField(auto_now_add=True)
    
    # Approval status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    approval_date = models.DateField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Associated user account (created during registration)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='company'
    )

    def __str__(self):
        return f"{self.official_name} ({self.status})"

    def approve(self, admin_user=None):
        """Approve company and activate their account"""
        if self.status == 'approved':
            return
            
        if self.status == 'rejected':
            raise ValueError('Cannot approve a rejected company')
            
        self.status = 'approved'
        self.approval_date = timezone.now()
        
        # Activate the associated user account
        self.user.is_active = True
        self.user.save()
        
        self.save()

    def reject(self, reason=None):
        """Reject company and deactivate their account"""
        if self.status == 'rejected':
            return
            
        self.status = 'rejected'
        self.rejection_reason = reason
        
        # Deactivate the associated user account
        self.user.is_active = False
        self.user.save()
        
        self.save()
