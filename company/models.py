from django.db import models
from django.core.validators import MinLengthValidator

class Company(models.Model):
    SECTOR_CHOICES = [
        ('manufacturing  & Production', 'Manufacturing & Production'),
        ('construction', 'Construction & Demolition'),
        ('retail', 'Wholesale & Retail'),
        ('packaging', 'Packaging & Printing'),
        ('recycling', 'Recycling & Waste Management'),
        ('Energy & Utilities', 'Energy & Utilities'),
        ('broker', 'Broker'),
        ('Other', 'Other')
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    official_name = models.CharField(max_length=255)
    vat_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[MinLengthValidator(8)]
    )
    email = models.EmailField(unique=True)
    sector = models.CharField(
        max_length=255,
        choices=SECTOR_CHOICES,
        default='manufacturing  & Production'
    )
    country = models.CharField(max_length=255)
    website = models.URLField(default='http://example.com')

    # Contact persons are now managed through User model with contact_type field
    # This provides proper normalization and allows unlimited contacts per company

    registration_date = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='Approval Status'
    )

    # Payment setup fields
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True, help_text="Stripe Connect account ID")
    stripe_capabilities_complete = models.BooleanField(default=False, help_text="Whether Stripe account has required capabilities")
    stripe_onboarding_complete = models.BooleanField(default=False, help_text="Whether Stripe onboarding is complete")
    payment_ready = models.BooleanField(default=False, db_index=True, help_text="Whether company can receive payments")
    last_payment_check = models.DateTimeField(blank=True, null=True, help_text="Last time payment readiness was verified")

    def __str__(self):
        return f"{self.official_name} ({self.status})"
