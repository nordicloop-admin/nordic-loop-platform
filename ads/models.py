from django.db import models
from category.models import Category,SubCategory

class Ad(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('lb', 'Pound'),
        ('ton', 'Ton')


    ]

    item_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    country_of_origin = models.CharField(max_length=255)
    end_date = models.DateField()
    end_time = models.TimeField()
    item_image = models.ImageField(upload_to='auction_images/', null=True, blank=True)

    def __str__(self):
        return self.item_name