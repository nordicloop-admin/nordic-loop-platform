from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from ads.models import Ad
from users.models import User

class Bid(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("outbid", "Outbid"),
        ("winning", "Winning"),
        ("won", "Won"),
        ("lost", "Lost"),
        ("cancelled", "Cancelled"),
    ]

    VOLUME_TYPE_CHOICES = [
        ("partial", "Partial Volume"),
        ("full", "Full Volume"),
    ]

    # Core bidding fields
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="bids")
    
    # Pricing
    bid_price_per_unit = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Bid price per unit of material"
    )
    
    # Volume and quantity
    volume_requested = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Quantity of material requested"
    )
    volume_type = models.CharField(
        max_length=10, 
        choices=VOLUME_TYPE_CHOICES, 
        default="partial"
    )
    
    # Calculated total value
    total_bid_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Automatically calculated: bid_price_per_unit * volume_requested"
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="active"
    )
    is_auto_bid = models.BooleanField(
        default=False,
        help_text="Whether this bid was placed automatically"
    )
    max_auto_bid_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Maximum price for auto-bidding"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Bid notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes or requirements from the bidder"
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'ad']  # One active bid per user per ad
        verbose_name = "Bid"
        verbose_name_plural = "Bids"
        indexes = [
            models.Index(fields=['ad', '-bid_price_per_unit']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.bid_price_per_unit} {self.ad.currency}/{self.ad.unit_of_measurement} on {self.ad.title}"

    def clean(self):
        """Validate bid against ad requirements"""
        if self.ad_id:
            # Check if ad allows bidding
            if not self.ad.is_active:
                raise ValidationError("Cannot bid on inactive ads.")
            
            # Check if user is not the ad owner
            if self.user == self.ad.user:
                raise ValidationError("You cannot bid on your own ad.")
            
            # Check minimum bid requirements
            if self.ad.starting_bid_price and self.bid_price_per_unit < self.ad.starting_bid_price:
                raise ValidationError(
                    f"Bid price must be at least {self.ad.starting_bid_price} {self.ad.currency}"
                )
            
            # Check volume requirements
            if self.ad.minimum_order_quantity and self.volume_requested < self.ad.minimum_order_quantity:
                raise ValidationError(
                    f"Volume must be at least {self.ad.minimum_order_quantity} {self.ad.unit_of_measurement}"
                )
            
            if self.volume_requested > self.ad.available_quantity:
                raise ValidationError(
                    f"Volume cannot exceed available quantity of {self.ad.available_quantity} {self.ad.unit_of_measurement}"
                )

    def save(self, *args, **kwargs):
        # Calculate total bid value
        if self.bid_price_per_unit and self.volume_requested:
            self.total_bid_value = self.bid_price_per_unit * self.volume_requested
        
        # Validate before saving
        self.clean()
        
        super().save(*args, **kwargs)

    @property
    def is_winning(self):
        """Check if this is currently the highest bid for this ad"""
        if self.status in ['won', 'lost', 'cancelled']:
            return False
        
        highest_bid = Bid.objects.filter(
            ad=self.ad,
            status__in=['active', 'winning']
        ).exclude(id=self.id).order_by('-bid_price_per_unit').first()
        
        return not highest_bid or self.bid_price_per_unit > highest_bid.bid_price_per_unit

    @property
    def rank(self):
        """Get the rank of this bid among all bids for this ad"""
        higher_bids = Bid.objects.filter(
            ad=self.ad,
            bid_price_per_unit__gt=self.bid_price_per_unit,
            status__in=['active', 'winning']
        ).count()
        return higher_bids + 1


class BidHistory(models.Model):
    """Track all bid changes for auditing"""
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name="history")
    previous_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    new_price = models.DecimalField(max_digits=12, decimal_places=2)
    previous_volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    new_volume = models.DecimalField(max_digits=10, decimal_places=2)
    change_reason = models.CharField(
        max_length=50,
        choices=[
            ('bid_placed', 'Bid Placed'),
            ('bid_updated', 'Bid Updated'),
            ('auto_bid', 'Auto Bid'),
            ('outbid', 'Outbid'),
        ]
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.bid} - {self.change_reason} at {self.timestamp}"



