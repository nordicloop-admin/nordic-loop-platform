from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import CustomUser


class Category(models.Model):
    """
    Categories for waste materials.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True) 
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name




class Auction(models.Model):
    """
    Represents an auction listing for waste materials.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='auctions'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='auctions'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    unit = models.CharField(max_length=50, help_text="Unit of measurement (e.g., kg, ton, m³)")
    location = models.CharField(max_length=255, help_text="Location of the waste material")
    starting_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    current_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Current highest bid price"
    )
    reserve_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Minimum price seller will accept"
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def is_active(self):
        """Check if the auction is currently active."""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now and
            self.end_date > now
        )

    def time_remaining(self):
        """Calculate time remaining in the auction."""
        if self.status != 'active':
            return None

        now = timezone.now()
        if now > self.end_date:
            return None

        return self.end_date - now

    def highest_bid(self):
        """Get the highest bid for this auction."""
        return self.bids.order_by('-amount').first()

    def bid_count(self):
        """Get the number of bids for this auction."""
        return self.bids.count()


class AuctionImage(models.Model):
    """
    Images for auction listings.
    """
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='auction_images/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        return f"Image for {self.auction.title}"


class Bid(models.Model):
    """
    Represents a bid placed on an auction.
    """
    auction = models.ForeignKey(
        Auction,
        on_delete=models.CASCADE,
        related_name='bids'
    )
    bidder = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='bids'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_winning = models.BooleanField(default=False)

    class Meta:
        ordering = ['-amount']

    def __str__(self):
        return f"{self.bidder.name} bid {self.amount} on {self.auction.title}"



