from django.contrib import admin
from django.utils.html import format_html
from .models import User, PasswordResetOTP

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "name",
        "company_name",
        "contact_type",
        "can_place_ads",
        "can_place_bids",
        "is_staff",
        "is_active",
        "is_superuser",
        "last_login",
        "date_joined",
        "role",
    ]
    list_filter = ["is_staff", "is_superuser", "is_active", "company", "contact_type", "role", "can_place_ads", "can_place_bids"]
    search_fields = ["username", "email", "first_name", "last_name", "name", "company__official_name"]
    ordering = ["-date_joined"]
    readonly_fields = ["last_login", "date_joined"]
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'name', 'password')
        }),
        ('Company & Contact', {
            'fields': ('company', 'contact_type', 'is_primary_contact', 'position')
        }),
        ('Permissions', {
            'fields': ('role', 'can_place_ads', 'can_place_bids', 'is_staff', 'is_active', 'is_superuser')
        }),
        ('Payment Information (Legacy)', {
            'fields': ('bank_country', 'bank_currency', 'bank_account_holder', 
                      'bank_account_number', 'bank_routing_number', 
                      'payout_frequency', 'payout_method'),
            'classes': ('collapse',),
            'description': 'Legacy payment fields - new payments use Company Stripe accounts'
        }),
        ('Groups & Permissions', {
            'fields': ('groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    def company_name(self, obj):
        """Display company name"""
        if obj.company:
            return obj.company.official_name
        return format_html('<span style="color: #999;">No Company</span>')
    company_name.short_description = 'Company'
    company_name.admin_order_field = 'company__official_name'

    def get_queryset(self, request):
        """Optimize queries for the list view"""
        return super().get_queryset(request).select_related('company')


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "email",
        "otp",
        "is_used",
        "is_valid_status",
        "created_at",
        "expires_at",
        "reset_token_display"
    ]
    list_filter = ["is_used", "created_at", "expires_at"]
    search_fields = ["email", "otp"]
    readonly_fields = ["created_at", "is_valid_status"]
    ordering = ["-created_at"]
    
    fieldsets = (
        ('OTP Information', {
            'fields': ('email', 'otp', 'reset_token')
        }),
        ('Status', {
            'fields': ('is_used', 'is_valid_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_valid_status(self, obj):
        """Show if OTP is currently valid"""
        return obj.is_valid()
    is_valid_status.boolean = True
    is_valid_status.short_description = 'Valid'

    def reset_token_display(self, obj):
        """Display reset token with formatting"""
        if obj.reset_token:
            return format_html(
                '<span style="font-family: monospace; background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">{}</span>',
                obj.reset_token[:20] + '...' if len(obj.reset_token) > 20 else obj.reset_token
            )
        return format_html('<span style="color: #999;">None</span>')
    reset_token_display.short_description = 'Reset Token'
    reset_token_display.admin_order_field = 'reset_token'
