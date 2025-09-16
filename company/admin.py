from django.contrib import admin
from django.utils.html import format_html
from company.models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'official_name', 'vat_number', 'email', 'country', 'sector',
        'status', 'registration_date', 'payment_ready', 'stripe_account_display', 'get_contacts_count'
    )
    list_filter = ('status', 'registration_date', 'sector', 'payment_ready', 'country', 
                   'stripe_onboarding_complete', 'stripe_capabilities_complete')
    search_fields = (
        'official_name', 'vat_number', 'email', 'stripe_account_id'
    )
    readonly_fields = ('registration_date', 'last_payment_check')
    list_editable = ('status', 'payment_ready')
    ordering = ['-registration_date']

    fieldsets = (
        ('Company Information', {
            'fields': ('official_name', 'vat_number', 'email', 'country', 'sector', 'website')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Payment Setup', {
            'fields': ('stripe_account_id', 'stripe_capabilities_complete', 'stripe_onboarding_complete', 
                      'payment_ready', 'last_payment_check'),
            'classes': ('collapse',),
            'description': 'Stripe Connect payment account information'
        }),
        ('Contact Information', {
            'description': 'Contact persons are managed through the User model. Use the Users admin to manage company contacts.',
            'fields': (),
        }),
        ('Timestamps', {
            'fields': ('registration_date',),
            'classes': ('collapse',)
        }),
    )

    def stripe_account_display(self, obj):
        """Display Stripe account ID with formatting"""
        if obj.stripe_account_id:
            return format_html(
                '<span style="font-family: monospace; background: #f0f0f0; padding: 2px 4px; border-radius: 3px;">{}</span>',
                obj.stripe_account_id
            )
        return format_html('<span style="color: #999;">No Account</span>')
    stripe_account_display.short_description = 'Stripe Account'
    stripe_account_display.admin_order_field = 'stripe_account_id'

    def get_contacts_count(self, obj):
        """Display number of contact users for this company"""
        from django.contrib.auth import get_user_model
        user_model = get_user_model()
        count = user_model.objects.filter(
            company=obj,
            contact_type__in=['primary', 'secondary']
        ).count()
        return f"{count} contacts"
    get_contacts_count.short_description = 'Contacts'

    def get_queryset(self, request):
        """Optimize queries for the list view"""
        return super().get_queryset(request).select_related()

    actions = ['approve_companies', 'reject_companies', 'check_payment_status']

    def approve_companies(self, request, queryset):
        """Bulk approve companies"""
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} companies were approved.')
    approve_companies.short_description = 'Approve selected companies'

    def reject_companies(self, request, queryset):
        """Bulk reject companies"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} companies were rejected.')
    reject_companies.short_description = 'Reject selected companies'

    def check_payment_status(self, request, queryset):
        """Check payment status for selected companies"""
        from company.stripe_service import StripeConnectService
        from django.utils import timezone
        
        updated_count = 0
        for company in queryset:
            if company.stripe_account_id:
                try:
                    StripeConnectService.check_account_status(company)
                    company.last_payment_check = timezone.now()
                    company.save()
                    updated_count += 1
                except Exception:
                    pass
        
        self.message_user(request, f'Payment status checked for {updated_count} companies.')
    check_payment_status.short_description = 'Check payment status for selected companies'
