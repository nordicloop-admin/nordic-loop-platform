from rest_framework import serializers
from .models import StripeAccount, PaymentIntent, Transaction, PayoutSchedule
from users.serializers import UserSerializer
from bids.serializer import BidSerializer


class StripeAccountSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = StripeAccount
        fields = [
            'id', 'user', 'user_email', 'user_name', 'stripe_account_id', 
            'account_status', 'bank_account_last4', 'bank_name', 'bank_country',
            'charges_enabled', 'payouts_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'stripe_account_id', 'created_at', 'updated_at']


class BankAccountSetupSerializer(serializers.Serializer):
    """Serializer for bank account setup data"""
    account_holder_name = serializers.CharField(max_length=255)
    account_number = serializers.CharField(max_length=50)
    routing_number = serializers.CharField(max_length=50, required=False)
    bank_name = serializers.CharField(max_length=255)
    bank_country = serializers.CharField(max_length=2, default='SE')
    currency = serializers.CharField(max_length=3, default='SEK')


class PaymentIntentSerializer(serializers.ModelSerializer):
    buyer_email = serializers.CharField(source='buyer.email', read_only=True)
    seller_email = serializers.CharField(source='seller.email', read_only=True)
    bid_details = BidSerializer(source='bid', read_only=True)
    
    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'stripe_payment_intent_id', 'bid', 'bid_details',
            'buyer', 'buyer_email', 'seller', 'seller_email',
            'total_amount', 'commission_amount', 'seller_amount', 'commission_rate',
            'status', 'currency', 'created_at', 'updated_at', 'confirmed_at'
        ]
        read_only_fields = ['id', 'stripe_payment_intent_id', 'created_at', 'updated_at', 'confirmed_at']


class PaymentIntentCreateSerializer(serializers.Serializer):
    """Serializer for creating payment intents"""
    bid_id = serializers.IntegerField()
    return_url = serializers.URLField(required=False)


class TransactionSerializer(serializers.ModelSerializer):
    from_user_email = serializers.CharField(source='from_user.email', read_only=True)
    to_user_email = serializers.CharField(source='to_user.email', read_only=True)
    payment_intent_details = PaymentIntentSerializer(source='payment_intent', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'payment_intent', 'payment_intent_details', 'transaction_type',
            'amount', 'currency', 'status', 'from_user', 'from_user_email',
            'to_user', 'to_user_email', 'stripe_transfer_id', 'stripe_charge_id',
            'description', 'metadata', 'created_at', 'updated_at', 'processed_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'processed_at']


class PayoutScheduleSerializer(serializers.ModelSerializer):
    seller_email = serializers.CharField(source='seller.email', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    processed_by_email = serializers.CharField(source='processed_by.email', read_only=True)
    transaction_count = serializers.IntegerField(source='transactions.count', read_only=True)
    
    class Meta:
        model = PayoutSchedule
        fields = [
            'id', 'seller', 'seller_email', 'seller_name', 'total_amount', 'currency',
            'status', 'scheduled_date', 'processed_date', 'transactions', 'transaction_count',
            'stripe_payout_id', 'created_by', 'created_by_email', 'processed_by', 
            'processed_by_email', 'notes', 'metadata', 'created_at', 'updated_at', 'is_overdue'
        ]
        read_only_fields = ['id', 'stripe_payout_id', 'created_at', 'updated_at', 'is_overdue']


class PayoutScheduleCreateSerializer(serializers.Serializer):
    """Serializer for creating payout schedules"""
    seller_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of seller user IDs to create payouts for"
    )
    scheduled_date = serializers.DateField(help_text="Date when the payout should be processed")
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class PayoutProcessSerializer(serializers.Serializer):
    """Serializer for processing payouts"""
    payout_schedule_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        help_text="List of payout schedule IDs to process"
    )
    force_process = serializers.BooleanField(
        default=False,
        help_text="Force processing even if scheduled date hasn't arrived"
    )


class PaymentStatsSerializer(serializers.Serializer):
    """Serializer for payment statistics"""
    total_payments = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_commission = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_payouts = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_payouts = serializers.DecimalField(max_digits=12, decimal_places=2)
    active_sellers = serializers.IntegerField()
    payment_count = serializers.IntegerField()
    commission_rate_avg = serializers.DecimalField(max_digits=5, decimal_places=2)
    currency = serializers.CharField(max_length=3)


class UserPaymentHistorySerializer(serializers.Serializer):
    """Serializer for user payment history"""
    user_id = serializers.IntegerField()
    user_email = serializers.CharField()
    total_spent = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_commission_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_count = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    pending_payouts = serializers.DecimalField(max_digits=12, decimal_places=2)
    last_payment_date = serializers.DateTimeField()
    last_payout_date = serializers.DateField()
