from django.db import models
from django.core.validators import MinLengthValidator
from users.models import CustomUser
from django.utils import timezone

class Account(models.Model):
    SUBSCRIPTION_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise')
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='account'
    )
    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_CHOICES,
        default='basic'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.subscription_type}"

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

    # Registration credentials
    email = models.EmailField(
        unique=True,
        help_text="This email will be used for login after approval"
    )
    password = models.CharField(
        max_length=128,  # Same as Django's default password field
        help_text="Temporary storage for registration password",
        blank=True,
        null=True
    )
    registration_date = models.DateField(auto_now_add=True)

    # Approval status - just a simple field
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    approval_date = models.DateField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.official_name} ({self.status})"
