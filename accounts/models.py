from django.db import models
from django.core.validators import MinLengthValidator
from users.models import CustomUser


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


    SECTOR_CHOICES = [
        ('manufacturing  & Production', 'Manufacturing & Production'),
        ('construction', 'Construction & Demolition'),
        ('retail', 'Wholesale & Retail'),
        # ('Chemical & Pharmaceutical', 'Chemical & Pharmaceutical'),
        ('packaging', 'Packaging & Printing'),
        ('recycling', 'Recycling & Waste Management'),
        ('Energy & Utilities', 'Energy & Utilities'),
        # other (optional)

    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    # Basic company information (collected during registration)
    vat_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='VAT Number',
        help_text='Format: Country code + 9-12 digits (e.g. BE0123456789)',
        validators=[MinLengthValidator(8)]
    )
    official_name = models.CharField(max_length=255, null = False)
    email = models.EmailField(unique=True)
    sector = models.CharField(
        max_length=255,
        choices=SECTOR_CHOICES,
        default='manufacturing'
    )
    website = models.URLField(blank=False, null=False)
    contact_name = models.CharField(
        max_length=255,
        verbose_name='Contact Name'
    )
    contact_position = models.CharField(
        max_length=255,
        verbose_name='Contact Position'
    )
    contact_email = models.EmailField(
        unique=True,
        verbose_name='Contact Email'
    )
    password = models.CharField(
        max_length=128,
        blank=False,
        null=False,
    )

    registration_date = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='Approval Status'
    )
    approval_date = models.DateField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.official_company_name} ({self.status})"
