from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class PricingPlan(models.Model):
    """
    Model for storing pricing plan information
    """
    PLAN_TYPES = [
        ('free', 'Free'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]

    name = models.CharField(max_length=100, help_text="Plan name (e.g., 'Free Plan')")
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Monthly price in SEK (0 for free plan)"
    )
    currency = models.CharField(max_length=3, default='SEK')
    color = models.CharField(max_length=7, default='#008066', help_text="Hex color code for the plan")
    is_popular = models.BooleanField(default=False, help_text="Mark as popular/recommended plan")
    is_active = models.BooleanField(default=True, help_text="Whether this plan is available for selection")
    order = models.IntegerField(default=0, help_text="Display order (lower numbers first)")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'price']
        verbose_name = "Pricing Plan"
        verbose_name_plural = "Pricing Plans"

    def __str__(self):
        return f"{self.name} - {self.price} {self.currency}/month"


class BaseFeature(models.Model):
    """
    Model for storing base features that can be reused across plans
    """
    FEATURE_CATEGORIES = [
        ('marketplace', 'Marketplace'),
        ('auctions', 'Auctions'),
        ('reporting', 'Reporting'),
        ('support', 'Support'),
        ('commission', 'Commission'),
        ('verification', 'Verification'),
        ('access', 'Access'),
        ('community', 'Community'),
    ]

    name = models.CharField(max_length=100, help_text="Internal name for the feature")
    category = models.CharField(max_length=20, choices=FEATURE_CATEGORIES, help_text="Feature category")
    base_description = models.TextField(help_text="Base description template (can use placeholders)")
    is_active = models.BooleanField(default=True, help_text="Whether this feature is available")
    order = models.IntegerField(default=0, help_text="Global display order")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order']
        verbose_name = "Base Feature"
        verbose_name_plural = "Base Features"

    def __str__(self):
        return f"{self.name} ({self.category})"


class PlanFeature(models.Model):
    """
    Model for linking plans to features with specific configurations
    """
    plan = models.ForeignKey(PricingPlan, on_delete=models.CASCADE, related_name='plan_features')
    base_feature = models.ForeignKey(BaseFeature, on_delete=models.CASCADE, related_name='plan_features')

    # Feature configuration for this plan
    is_included = models.BooleanField(default=True, help_text="Whether this feature is included in the plan")
    custom_description = models.TextField(blank=True, null=True, help_text="Custom description for this plan (overrides base)")
    feature_value = models.CharField(max_length=100, blank=True, null=True, help_text="Specific value for this plan (e.g., 'Unlimited', '9%', 'Limited')")

    # Display settings
    order = models.IntegerField(default=0, help_text="Display order within the plan")
    is_highlighted = models.BooleanField(default=False, help_text="Highlight this feature as a key benefit")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        unique_together = ['plan', 'base_feature']
        verbose_name = "Plan Feature"
        verbose_name_plural = "Plan Features"

    def __str__(self):
        return f"{self.plan.name} - {self.base_feature.name}"

    @property
    def display_text(self):
        """Get the display text for this feature"""
        if self.custom_description:
            return self.custom_description

        # Use base description with value substitution
        description = self.base_feature.base_description
        if self.feature_value and '{value}' in description:
            description = description.replace('{value}', self.feature_value)

        return description


class PricingPageContent(models.Model):
    """
    Model for storing pricing page header content
    """
    title = models.CharField(max_length=200, default="Flexible Business Plans for Sustainable Growth")
    subtitle = models.TextField(default="Flexible plans for every business; whether you're just starting or looking to scale sustainability.")
    section_label = models.CharField(max_length=50, default="Pricing")
    
    # CTA settings
    cta_text = models.CharField(max_length=50, default="Get Started")
    cta_url = models.CharField(max_length=200, default="/coming-soon")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Pricing Page Content"
        verbose_name_plural = "Pricing Page Content"
    
    def __str__(self):
        return f"Pricing Page Content - {self.title[:30]}..."
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and PricingPageContent.objects.exists():
            raise ValueError("Only one PricingPageContent instance is allowed")
        super().save(*args, **kwargs)
