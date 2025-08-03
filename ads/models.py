from django.db import models
from category.models import Category, SubCategory, CategorySpecification
from company.models import Company
from users.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from base.fields import FirebaseImageField


class Location(models.Model):
    """Location model for storing detailed address information"""
    country = models.CharField(max_length=100, default='Sweden')
    state_province = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)
    address_line = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.city}, {self.state_province}, {self.country}"


class Ad(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('tons', 'Tons'),
        ('tonnes', 'Tonnes'),
        ('lbs', 'Pounds'),
        ('pounds', 'Pounds'),
        ('pieces', 'Pieces'),
        ('units', 'Units'),
        ('bales', 'Bales'),
        ('containers', 'Containers'),
        ('m³', 'Cubic Meters'),
        ('cubic_meters', 'Cubic Meters'),
        ('liters', 'Liters'),
        ('gallons', 'Gallons'),
        ('meters', 'Meters'),
    ]

    SELLING_TYPE_CHOICES = [
        ('partition', 'Selling in Partition'),
        ('whole', 'Selling as Whole'),
        ('both whole and partion', 'selling as whole and partion'),
    ]

    MATERIAL_FREQUENCY_CHOICES = [
        ("one_time", "One-time"),
        ("weekly", "Weekly"),
        ("bi_weekly", "Bi-weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    MATERIAL_ORIGIN = [
        ('post_industrial', 'Post-industrial'),
        ('post_consumer', 'Post-consumer'),
        ('mix', 'Mix')
    ]

    MATERIAL_CONTAMINATION = [
        ('clean', 'Clean'),
        ('slightly_contaminated', 'Slightly Contaminated'),
        ('heavily_contaminated', 'Heavily Contaminated')
    ]

    ADDITIVES_CHOICES = [
        ('uv_stabilizer', 'UV Stabilizer'),
        ('antioxidant', 'Antioxidant'),
        ('flame_retardants', 'Flame retardants'),
        ('chlorides', 'Chlorides'),
        ('no_additives', 'No additives')
    ]

    STORAGE_CONDITIONS = [
        ('climate_controlled', 'Climate Controlled'),
        ('protected_outdoor', 'Protected Outdoor'),
        ('unprotected_outdoor', 'Unprotected Outdoor')
    ]

    PACKAGING_CHOICES = [
        ('baled', 'Baled'),
        ('loose', 'Loose'),
        ('big_bag', 'Big-bag'),
        ('octabin', 'Octabin'),
        ('roles', 'Roles'),
        ('container', 'Container'),
        ('other', 'Other')
    ]

    PROCESSING_CHOICES = [
        ('blow_moulding', 'Blow moulding'),
        ('injection_moulding', 'Injection moulding'),
        ('extrusion', 'Extrusion'),
        ('calendering', 'Calendering'),
        ('rotational_moulding', 'Rotational moulding'),
        ('sintering', 'Sintering'),
        ('thermoforming', 'Thermoforming')
    ]

    DELIVERY_OPTIONS = [
        ('pickup_only', 'Pickup Only'),
        ('local_delivery', 'Local Delivery'),
        ('national_shipping', 'National Shipping'),
        ('international_shipping', 'International Shipping'),
        ('freight_forwarding', 'Freight Forwarding')
    ]

    CURRENCY_CHOICES = [
        ('EUR', 'Euro'),
        ('USD', 'US Dollar'),
        ('SEK', 'Swedish Krona'),
        ('GBP', 'British Pound'),
    ]

    AUCTION_DURATION_CHOICES = [
        (1, '1 day'),
        (3, '3 days'),
        (7, '7 days'),
        (14, '14 days'),
        (30, '30 days'),
        (0, 'Custom'),  # 0 will represent custom duration
    ]

    # Basic Information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ads", blank=True, null=True)
    
    # Step 1: Material Type
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, null=True, blank=True)
    specific_material = models.TextField(blank=True, null=True, help_text="e.g., Grade 5052 Aluminum, HDPE milk bottles, etc.")
    packaging = models.CharField(max_length=50, choices=PACKAGING_CHOICES, null=True, blank=True)
    material_frequency = models.CharField(max_length=20, choices=MATERIAL_FREQUENCY_CHOICES, null=True, blank=True)

    # Step 2: Specifications
    specification = models.OneToOneField(CategorySpecification, on_delete=models.SET_NULL, null=True, blank=True)
    additional_specifications = models.TextField(blank=True, null=True, help_text="e.g., Melt Flow Index: 2.5, Density: 0.95 g/cm³")

    # Step 3: Material Origin
    origin = models.CharField(max_length=20, choices=MATERIAL_ORIGIN, null=True, blank=True)

    # Step 4: Contamination
    contamination = models.CharField(max_length=30, choices=MATERIAL_CONTAMINATION, null=True, blank=True)
    additives = models.CharField(max_length=30, choices=ADDITIVES_CHOICES, null=True, blank=True)
    storage_conditions = models.CharField(max_length=30, choices=STORAGE_CONDITIONS, null=True, blank=True)

    # Step 5: Processing Methods (can be multiple)
    processing_methods = models.JSONField(default=list, blank=True, help_text="List of applicable processing methods")

    # Step 6: Location & Logistics
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    pickup_available = models.BooleanField(default=False)
    delivery_options = models.JSONField(default=list, blank=True, help_text="List of available delivery options")

    # Step 7: Quantity & Pricing
    available_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total quantity available for auction"
    )
    unit_of_measurement = models.CharField(max_length=15, choices=UNIT_CHOICES, default='tons')
    minimum_order_quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Minimum quantity buyers must purchase (0 for no minimum)"
    )
    
    # Auction Pricing
    starting_bid_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Initial bid price per unit"
    )
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='EUR')
    auction_duration = models.IntegerField(choices=AUCTION_DURATION_CHOICES, default=7)
    custom_auction_duration = models.IntegerField(
        blank=True, 
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Custom auction duration in days (used when auction_duration is set to 'Custom')"
    )
    reserve_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="If no bids reach this price, the auction will not complete"
    )
    
    # Step 8: Title, Description & Image
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    keywords = models.CharField(max_length=500, blank=True, null=True, help_text="Keywords separated by commas")
    material_image = FirebaseImageField(folder='material_images', blank=True, null=True)
    
    # System fields
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('suspended', 'Suspended by Admin')
    ], default='active')
    suspended_by_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auction_start_date = models.DateTimeField(blank=True, null=True)
    auction_end_date = models.DateTimeField(blank=True, null=True)

    # Broker permissions
    allow_broker_bids = models.BooleanField(
        default=True,
        help_text="Allow brokers to place bids on this material"
    )
    
    # Form step tracking
    current_step = models.IntegerField(default=1)
    is_complete = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Material Ad"
        verbose_name_plural = "Material Ads"

    def __str__(self):
        return f"{self.title}" if self.title else f"Ad #{self.id}"

    @property
    def total_starting_value(self):
        """Calculate total starting value"""
        if self.starting_bid_price and self.available_quantity:
            return self.starting_bid_price * self.available_quantity
        return Decimal('0.00')

    @property
    def effective_auction_duration(self):
        """Get the effective auction duration in days"""
        if self.auction_duration == 0:  # Custom
            return self.custom_auction_duration if self.custom_auction_duration else 7
        return self.auction_duration

    def get_auction_duration_display(self):
        """Get human-readable auction duration"""
        if self.auction_duration == 0:  # Custom
            if self.custom_auction_duration:
                return f"{self.custom_auction_duration} days (Custom)"
            return "Custom (not set)"
        return dict(self.AUCTION_DURATION_CHOICES).get(self.auction_duration, f"{self.auction_duration} days")

    def get_step_completion_status(self):
        """Return completion status for each step"""
        # Check if this is a plastic material (category_id 1 is assumed to be plastic)
        is_plastic = self.category and self.category.id == 1
        
        if is_plastic:
            # Full pathway for plastics
            return {
                1: bool(self.category and self.subcategory and self.packaging and self.material_frequency),
                2: bool(self.specification or self.additional_specifications),
                3: bool(self.origin),
                4: bool(self.contamination and self.additives and self.storage_conditions),
                5: bool(self.processing_methods),
                6: bool(self.location and self.delivery_options),
                7: bool(self.available_quantity and self.starting_bid_price and self.currency),
                8: bool(self.title and self.description),
            }
        else:
            # Shortened pathway for other materials - keeping original step numbers
            return {
                1: bool(self.category and self.subcategory and self.packaging and self.material_frequency),
                6: bool(self.location and self.delivery_options),  # Location & Logistics
                7: bool(self.available_quantity and self.starting_bid_price and self.currency),  # Quantity & Price
                8: bool(self.title and self.description),  # Image & Description
            }

    def is_step_complete(self, step_number):
        """Check if a specific step is complete"""
        return self.get_step_completion_status().get(step_number, False)

    def get_next_incomplete_step(self):
        """Get the next incomplete step number"""
        status = self.get_step_completion_status()
        # Check if this is a plastic material (category_id 1 is assumed to be plastic)
        is_plastic = self.category and self.category.id == 1
        
        if is_plastic:
            # Full pathway for plastics (steps 1-8)
            steps_to_check = range(1, 9)
        else:
            # Shortened pathway for other materials (steps 1, 6, 7, 8)
            steps_to_check = [1, 6, 7, 8]
            
        for step in steps_to_check:
            if not status.get(step, False):
                return step
        return None

class Subscription(models.Model):
    PLAN_CHOICES = [
        ("free", "Free"),
        ("standard", "Standard"),
        ("premium", "Premium"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("payment_failed", "Payment Failed"),
    ]
    # Payment method choices removed as per request
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    start_date = models.DateField()
    end_date = models.DateField()
    auto_renew = models.BooleanField(default=True)
    # payment_method field removed as per request
    last_payment = models.DateField()
    amount = models.CharField(max_length=50)
    contact_name = models.CharField(max_length=255)
    contact_email = models.EmailField()

    def __str__(self):
        return f"{self.company.official_name} - {self.plan} ({self.status})"

class Address(models.Model):
    TYPE_CHOICES = [
        ("business", "Business"),
        ("shipping", "Shipping"),
        ("billing", "Billing"),
    ]
    company = models.ForeignKey('company.Company', on_delete=models.CASCADE, related_name='addresses')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    contact_name = models.CharField(max_length=255)
    contact_phone = models.CharField(max_length=50)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.official_name} - {self.type} - {self.address_line1}"