# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
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
    


