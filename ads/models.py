from django.db import models
from category.models import Category,SubCategory
from users.models import User


class Ad(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('lb', 'Pound'),
        ('ton', 'Ton')
    ]

    SELLING_TYPE_CHOICES = [
        ('partition', 'Selling in Partition'),
        ('whole', 'Selling as Whole'),
        ('both whole and partion', 'selling as whole and partion'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ads", blank=True, null=True)
    item_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_partition = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    volume = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    selling_type = models.CharField(
        max_length=255,
        choices=SELLING_TYPE_CHOICES,
        default='whole',
        null=True
    )
    country_of_origin = models.CharField(max_length=255)
    end_date = models.DateField()
    end_time = models.TimeField()
    item_image = models.ImageField(upload_to='auction_images/', null=True, blank=True)

    def __str__(self):
        return self.item_name