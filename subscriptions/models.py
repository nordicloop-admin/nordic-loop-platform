from django.db import models
from django.utils import timezone
from users.models import CustomUser


class SubscriptionPlan(models.Model):
    """
    Represents a subscription plan with features and pricing.
    """
    PLAN_TYPE_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise')
    ]

    name = models.CharField(max_length=100)
    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPE_CHOICES,
        default='basic'
    )
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_plan_type_display()})"


class SubscriptionFeature(models.Model):
    """
    Represents a feature that can be included in subscription plans.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    plans = models.ManyToManyField(
        SubscriptionPlan,
        related_name='features'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    """
    Represents a user's subscription to a plan.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending')
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='user_subscriptions'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.get_status_display()})"

    def is_active(self):
        """Check if the subscription is currently active."""
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now and
            (self.end_date is None or self.end_date > now)
        )

    def days_remaining(self):
        """Calculate days remaining in the subscription."""
        if not self.end_date or self.status != 'active':
            return 0

        now = timezone.now()
        if now > self.end_date:
            return 0

        time_remaining = self.end_date - now
        return time_remaining.days

    def cancel(self):
        """Cancel the subscription."""
        self.status = 'cancelled'
        self.auto_renew = False
        self.save()

    def renew(self, days=None):
        """Renew the subscription for another period."""
        if not days:
            days = self.plan.duration_days

        self.status = 'active'

        # If already expired, start from now
        now = timezone.now()
        if not self.end_date or self.end_date < now:
            self.start_date = now
            self.end_date = now + timezone.timedelta(days=days)
        else:
            # Extend from current end date
            self.end_date = self.end_date + timezone.timedelta(days=days)

        self.save()


class SubscriptionHistory(models.Model):
    """
    Tracks the history of subscription changes.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('renewed', 'Renewed'),
        ('cancelled', 'Cancelled'),
        ('changed', 'Plan Changed'),
        ('expired', 'Expired')
    ]

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='history'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES
    )
    from_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='history_from',
        null=True,
        blank=True
    )
    to_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='history_to',
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.subscription.user.email} - {self.get_action_display()} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Subscription histories"