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
        ('Other', 'Other')

    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    official_name = models.CharField(max_length=255, null = False)
    vat_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[MinLengthValidator(8)]
    )
    email = models.EmailField(unique=True)
    sector = models.CharField(
        max_length=255,
        choices=SECTOR_CHOICES,
        default='manufacturing'
    )
    country = models.CharField(max_length=255, null = False)
    website = models.URLField(blank=False, null=False, default='http://example.com')
    contact_name = models.CharField(
        max_length=255,
        verbose_name='Contact Name',
        null=True,
        blank=True
    )
    contact_position = models.CharField(
        max_length=255,
        verbose_name='Contact Position',
        null=True,
        blank=True
    )
    contact_email = models.EmailField(
        unique=True,
    )

    registration_date = models.DateField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        verbose_name='Approval Status'
    )
   

    def __str__(self):
        return f"{self.official_name} ({self.status})"
    

