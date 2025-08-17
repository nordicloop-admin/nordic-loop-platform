from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import StripeAccount, PaymentIntent, Transaction, PayoutSchedule


@admin.register(StripeAccount)
class StripeAccountAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'stripe_account_id', 'account_status', 'charges_enabled', 'payouts_enabled', 'created_at')
    list_filter = ('account_status', 'charges_enabled', 'payouts_enabled', 'created_at')
    search_fields = ('user__email', 'stripe_account_id', 'bank_name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = ('stripe_payment_intent_id', 'buyer_email', 'seller_email', 'total_amount', 'commission_amount', 'status', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('stripe_payment_intent_id', 'buyer__email', 'seller__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'confirmed_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('stripe_payment_intent_id', 'bid', 'status', 'currency')
        }),
        ('Users', {
            'fields': ('buyer', 'seller')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'commission_amount', 'seller_amount', 'commission_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'confirmed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def buyer_email(self, obj):
        return obj.buyer.email
    buyer_email.short_description = 'Buyer'
    buyer_email.admin_order_field = 'buyer__email'
    
    def seller_email(self, obj):
        return obj.seller.email
    seller_email.short_description = 'Seller'
    seller_email.admin_order_field = 'seller__email'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_type', 'amount', 'currency', 'status', 'from_user_email', 'to_user_email', 'created_at')
    list_filter = ('transaction_type', 'status', 'currency', 'created_at')
    search_fields = ('stripe_transfer_id', 'stripe_charge_id', 'from_user__email', 'to_user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'processed_at')
    
    fieldsets = (
        ('Transaction Information', {
            'fields': ('transaction_type', 'amount', 'currency', 'status', 'description')
        }),
        ('Users', {
            'fields': ('from_user', 'to_user')
        }),
        ('Payment Intent', {
            'fields': ('payment_intent',)
        }),
        ('Stripe References', {
            'fields': ('stripe_transfer_id', 'stripe_charge_id')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def from_user_email(self, obj):
        return obj.from_user.email if obj.from_user else '-'
    from_user_email.short_description = 'From User'
    from_user_email.admin_order_field = 'from_user__email'
    
    def to_user_email(self, obj):
        return obj.to_user.email if obj.to_user else '-'
    to_user_email.short_description = 'To User'
    to_user_email.admin_order_field = 'to_user__email'


@admin.register(PayoutSchedule)
class PayoutScheduleAdmin(admin.ModelAdmin):
    list_display = ('seller_email', 'total_amount', 'currency', 'scheduled_date', 'status', 'is_overdue_display', 'created_by_email')
    list_filter = ('status', 'currency', 'scheduled_date', 'created_at')
    search_fields = ('seller__email', 'stripe_payout_id', 'created_by__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'is_overdue')
    
    fieldsets = (
        ('Payout Information', {
            'fields': ('seller', 'total_amount', 'currency', 'status')
        }),
        ('Schedule', {
            'fields': ('scheduled_date', 'processed_date')
        }),
        ('Stripe Reference', {
            'fields': ('stripe_payout_id',)
        }),
        ('Admin Information', {
            'fields': ('created_by', 'processed_by', 'notes')
        }),
        ('Related Transactions', {
            'fields': ('transactions',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'is_overdue'),
            'classes': ('collapse',)
        }),
    )
    
    def seller_email(self, obj):
        return obj.seller.email
    seller_email.short_description = 'Seller'
    seller_email.admin_order_field = 'seller__email'
    
    def created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else '-'
    created_by_email.short_description = 'Created By'
    created_by_email.admin_order_field = 'created_by__email'
    
    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red;">Yes</span>')
        return 'No'
    is_overdue_display.short_description = 'Overdue'
    is_overdue_display.admin_order_field = 'scheduled_date'
