from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone
import uuid


class StripeAccount(models.Model):
    """
    Model to store Stripe Connect account information for sellers
    """
    ACCOUNT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('restricted', 'Restricted'),
        ('inactive', 'Inactive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='stripe_account')
    stripe_account_id = models.CharField(max_length=255, unique=True)
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='pending')
    
    # Bank account details (encrypted in production)
    bank_account_last4 = models.CharField(max_length=4, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    bank_country = models.CharField(max_length=2, blank=True, null=True)
    
    # Account capabilities
    charges_enabled = models.BooleanField(default=False)
    payouts_enabled = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Stripe Account"
        verbose_name_plural = "Stripe Accounts"
        
    def __str__(self):
        return f"{self.user.email} - {self.stripe_account_id}"


class PaymentIntent(models.Model):
    """
    Model to track Stripe Payment Intents for bid payments
    """
    PAYMENT_STATUS_CHOICES = [
        ('requires_payment_method', 'Requires Payment Method'),
        ('requires_confirmation', 'Requires Confirmation'),
        ('requires_action', 'Requires Action'),
        ('processing', 'Processing'),
        ('requires_capture', 'Requires Capture'),
        ('canceled', 'Canceled'),
        ('succeeded', 'Succeeded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    
    # Related objects
    bid = models.OneToOneField('bids.Bid', on_delete=models.CASCADE, related_name='payment_intent')
    buyer = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='payment_intents')
    seller = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='received_payments')
    
    # Payment details
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    seller_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    
    # Status and metadata
    status = models.CharField(max_length=30, choices=PAYMENT_STATUS_CHOICES, default='requires_payment_method')
    currency = models.CharField(max_length=3, default='SEK')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Payment Intent"
        verbose_name_plural = "Payment Intents"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Payment {self.stripe_payment_intent_id} - {self.total_amount} {self.currency}"
    
    @property
    def is_successful(self):
        return self.status == 'succeeded'


class Transaction(models.Model):
    """
    Model to track all payment transactions and commission splits
    """
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('commission', 'Commission'),
        ('payout', 'Payout'),
        ('refund', 'Refund'),
    ]
    
    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_intent = models.ForeignKey(PaymentIntent, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='SEK')
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    
    # Related users
    from_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='outgoing_transactions', null=True, blank=True)
    to_user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='incoming_transactions', null=True, blank=True)
    
    # Stripe references
    stripe_transfer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Metadata
    description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.transaction_type.title()} - {self.amount} {self.currency}"


class PayoutSchedule(models.Model):
    """
    Model to manage payout schedules for sellers
    """
    PAYOUT_STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='payout_schedules')
    
    # Payout details
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='SEK')
    status = models.CharField(max_length=20, choices=PAYOUT_STATUS_CHOICES, default='scheduled')
    
    # Schedule information
    scheduled_date = models.DateField()
    processed_date = models.DateField(blank=True, null=True)
    
    # Related transactions
    transactions = models.ManyToManyField(Transaction, related_name='payout_schedules', blank=True)
    
    # Stripe reference
    stripe_payout_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Admin information
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_payouts')
    processed_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payouts')
    
    # Metadata
    notes = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Payout Schedule"
        verbose_name_plural = "Payout Schedules"
        ordering = ['-scheduled_date']
        
    def __str__(self):
        return f"Payout for {self.seller.email} - {self.total_amount} {self.currency} on {self.scheduled_date}"
    
    @property
    def is_overdue(self):
        return self.status == 'scheduled' and self.scheduled_date < timezone.now().date()
