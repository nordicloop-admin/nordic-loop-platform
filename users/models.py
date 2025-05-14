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

    name = models.CharField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    can_place_ads = models.BooleanField(default=False)
    can_place_bids = models.BooleanField(default=False)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="Staff", null=True, blank=True)
    

