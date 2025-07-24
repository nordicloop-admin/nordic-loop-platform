from django.db import models
from django.conf import settings
from category.models import Category, SubCategory

class CategorySubscription(models.Model):
    """
    Model for storing user subscriptions to categories and subcategories.
    Users can subscribe to either a whole category or specific subcategories.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='category_subscriptions'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    subcategory = models.ForeignKey(
        SubCategory,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Category Subscription"
        verbose_name_plural = "Category Subscriptions"
        unique_together = ['user', 'category', 'subcategory']
        
    def __str__(self):
        if self.subcategory:
            return f"{self.user.username} - {self.category.name} - {self.subcategory.name}"
        return f"{self.user.username} - {self.category.name}"
