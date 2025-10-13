# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import datetime
from company.models import Company

class User(AbstractUser):
    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Staff", "Staff"),
        ("Viewer", "Viewer"),
    ]

    CONTACT_TYPE_CHOICES = [
        ('primary', 'Primary Contact'),
        ('secondary', 'Secondary Contact'),
        ('regular', 'Regular User'),
    ]

    name = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    can_place_ads = models.BooleanField(default=False)
    can_place_bids = models.BooleanField(default=False)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="Staff", null=True, blank=True)

    # New fields for company contact normalization
    is_primary_contact = models.BooleanField(default=False, help_text="Indicates if this user is the primary contact for their company")
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES, default='regular', help_text="Type of contact this user represents")
    position = models.CharField(max_length=255, blank=True, null=True, help_text="Job position/title of the user")
    
    # Payment-related fields (for backward compatibility with existing database schema)
    bank_country = models.CharField(max_length=2, default='SE', help_text="Bank country code for payment processing")
    bank_currency = models.CharField(max_length=3, default='SEK', help_text="Bank currency for payment processing")
    bank_account_holder = models.CharField(max_length=255, blank=True, null=True, help_text="Bank account holder name")
    bank_account_number = models.CharField(max_length=255, blank=True, null=True, help_text="Bank account number")
    bank_routing_number = models.CharField(max_length=255, blank=True, null=True, help_text="Bank routing number")
    payout_frequency = models.CharField(max_length=20, default='weekly', help_text="Frequency of payouts")
    payout_method = models.CharField(max_length=20, default='bank_transfer', help_text="Method of payout")
    

class PasswordResetOTP(models.Model):
    """Model for storing password reset OTPs"""
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    reset_token = models.CharField(max_length=100, null=True, blank=True)
    # purpose distinguishes between password resets and account activation
    purpose = models.CharField(
        max_length=30,
        default='password_reset',
        choices=[('password_reset', 'Password Reset'), ('account_activation', 'Account Activation')]
    )
    
    def __str__(self):
        return f"{self.email} - {self.otp}"
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        return not self.is_used and timezone.now() <= self.expires_at
    
    @classmethod
    def generate_otp(cls, email, expiry_minutes=30, purpose: str = 'password_reset'):
        """Generate a new OTP for the given email and purpose"""
        import random
        import string
        
        # Generate a 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Calculate expiry time
        expires_at = timezone.now() + datetime.timedelta(minutes=expiry_minutes)
        
        # Create and save the OTP
        otp_obj = cls(email=email, otp=otp, expires_at=expires_at, purpose=purpose)
        otp_obj.save()
        return otp_obj
    
    @classmethod
    def verify_otp(cls, email, otp, purpose: str = 'password_reset'):
        """Verify if the OTP is valid for the given email and purpose"""
        try:
            # Get the latest OTP for the email
            otp_obj = cls.objects.filter(
                email=email,
                otp=otp,
                is_used=False,
                purpose=purpose
            ).latest('created_at')
            
            if otp_obj.is_valid():
                return otp_obj
            return None
        except cls.DoesNotExist:
            return None
    
    def mark_as_used(self):
        """Mark the OTP as used"""
        self.is_used = True
        self.save()
        
    def generate_token(self):
        """Generate a secure token for password reset"""
        import secrets
        
        self.reset_token = secrets.token_urlsafe(32)
        self.save()
        
        return self.reset_token
