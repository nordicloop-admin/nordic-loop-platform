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
    routing_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    bank_name = serializers.CharField(max_length=255)
    bank_country = serializers.CharField(max_length=2, default='SE')
    currency = serializers.CharField(max_length=3, default='SEK')


class PaymentIntentSerializer(serializers.ModelSerializer):
    buyer_email = serializers.CharField(source='buyer.email', read_only=True)
    seller_email = serializers.CharField(source='seller.email', read_only=True)
    buyer_company_name = serializers.CharField(source='buyer.company.official_name', read_only=True)
    seller_company_name = serializers.CharField(source='seller.company.official_name', read_only=True)
    auction_title = serializers.CharField(source='bid.ad.title', read_only=True)
    auction_id = serializers.IntegerField(source='bid.ad.id', read_only=True)
    bid_id = serializers.IntegerField(source='bid.id', read_only=True)
    bid_details = BidSerializer(source='bid', read_only=True)
    
    class Meta:
        model = PaymentIntent
        fields = [
            'id', 'stripe_payment_intent_id', 'bid', 'bid_details',
            'buyer', 'buyer_email', 'buyer_company_name', 'seller', 'seller_email', 'seller_company_name',
            'total_amount', 'commission_amount', 'seller_amount', 'commission_rate',
            'status', 'currency', 'created_at', 'updated_at', 'confirmed_at',
            'auction_title', 'auction_id', 'bid_id'
        ]
        read_only_fields = ['id', 'stripe_payment_intent_id', 'created_at', 'updated_at', 'confirmed_at']


class PaymentIntentCreateSerializer(serializers.Serializer):
    """Serializer for creating payment intents"""
    bid_id = serializers.IntegerField()
    return_url = serializers.URLField(required=False)


class TransactionSerializer(serializers.ModelSerializer):
    from_user_email = serializers.CharField(source='from_user.email', read_only=True)
    to_user_email = serializers.CharField(source='to_user.email', read_only=True)
    buyer_company_name = serializers.CharField(source='from_user.company.official_name', read_only=True)
    seller_company_name = serializers.CharField(source='to_user.company.official_name', read_only=True)
    auction_title = serializers.CharField(source='payment_intent.bid.ad.title', read_only=True)
    auction_id = serializers.IntegerField(source='payment_intent.bid.ad.id', read_only=True)
    payment_intent_details = PaymentIntentSerializer(source='payment_intent', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'payment_intent', 'payment_intent_details', 'transaction_type',
            'amount', 'currency', 'status', 'from_user', 'from_user_email', 'buyer_company_name',
            'to_user', 'to_user_email', 'seller_company_name', 'stripe_transfer_id', 'stripe_charge_id',
            'description', 'metadata', 'created_at', 'updated_at', 'processed_at',
            'auction_title', 'auction_id'
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


class UserTransactionSerializer(serializers.ModelSerializer):
    """Simplified transaction serializer for user dashboard - only essential fields"""
    auction_title = serializers.CharField(source='payment_intent.bid.ad.title', read_only=True)
    transaction_date = serializers.DateTimeField(source='created_at', read_only=True)
    
    # Determine user role in this transaction
    user_role = serializers.SerializerMethodField()
    other_party_email = serializers.SerializerMethodField()
    other_party_company = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'transaction_type',
            'amount',
            'currency',
            'status',
            'description',
            'transaction_date',
            'auction_title',
            'user_role',
            'other_party_email',
            'other_party_company'
        ]
    
    def get_user_role(self, obj):
        """Determine if current user is buyer or seller"""
        request = self.context.get('request')
        if not request or not request.user:
            return 'unknown'
        
        if obj.from_user == request.user:
            return 'buyer'  # User paid money
        elif obj.to_user == request.user:
            return 'seller'  # User received money
        else:
            return 'unknown'
    
    def get_other_party_email(self, obj):
        """Get the email of the other party in the transaction"""
        request = self.context.get('request')
        if not request or not request.user:
            return None
        
        if obj.from_user == request.user:
            return obj.to_user.email if obj.to_user else None
        elif obj.to_user == request.user:
            return obj.from_user.email if obj.from_user else None
        else:
            return None
    
    def get_other_party_company(self, obj):
        """Get the company name of the other party in the transaction"""
        request = self.context.get('request')
        if not request or not request.user:
            return None
        
        if obj.from_user == request.user:
            return obj.to_user.company.official_name if obj.to_user and obj.to_user.company else None
        elif obj.to_user == request.user:
            return obj.from_user.company.official_name if obj.from_user and obj.from_user.company else None
        else:
            return None


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


class SellerInfoSerializer(serializers.Serializer):
    """Serializer for seller information in pending payouts"""
    id = serializers.IntegerField()
    email = serializers.CharField()
    name = serializers.CharField()


class PendingPayoutSerializer(serializers.Serializer):
    """Serializer for pending payout data"""
    seller = SellerInfoSerializer()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = serializers.IntegerField()
    oldest_transaction = serializers.DateTimeField()

    def to_representation(self, instance):
        # Transform the data to match the expected format
        return {
            'seller': {
                'id': instance['seller'].id,
                'email': instance['seller'].email,
                'name': instance['seller'].get_full_name() or instance['seller'].email,
            },
            'total_amount': str(instance['total_amount']),
            'transaction_count': instance['transaction_count'],
            'oldest_transaction': instance['oldest_transaction'].isoformat(),
        }


class PendingPayoutsResponseSerializer(serializers.Serializer):
    """Serializer for pending payouts response"""
    success = serializers.BooleanField()
    pending_payouts = PendingPayoutSerializer(many=True)
    total_sellers = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
