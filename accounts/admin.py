from django.contrib import admin
from django.contrib import messages
from .models import Company, Account
from users.models import CustomUser

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_type', 'is_active', 'created_at')
    list_filter = ('subscription_type', 'is_active', 'created_at')
    search_fields = ('user__email', 'user__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'subscription_type', 'is_active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('official_name', 'vat_number', 'email', 'status', 'registration_date')
    list_filter = ('status', 'registration_date')
    search_fields = ('official_name', 'vat_number', 'email')
    readonly_fields = ('registration_date', 'approval_date')

    fieldsets = (
        ('Company Information', {
            'fields': ('official_name', 'vat_number', 'business_address',
                      'phone_number', 'website', 'status')
        }),
        ('Registration Credentials', {
            'fields': ('email', 'password')
        }),
        ('Dates', {
            'fields': ('registration_date', 'approval_date')
        }),
    )

    actions = ['approve_companies', 'reject_companies']

    def save_model(self, request, obj, form, change):
        try:
            if change and 'status' in form.changed_data:
                if obj.status == 'approved':
                    CustomUser.objects.approve_company(obj.id, admin_user=request.user)
                    messages.success(request, f'Company "{obj.official_name}" has been approved.')
                elif obj.status == 'rejected':
                    CustomUser.objects.reject_company(obj.id)
                    messages.success(request, f'Company "{obj.official_name}" has been rejected.')
            super().save_model(request, obj, form, change)
        except ValueError as e:
            messages.error(request, str(e))
            obj.refresh_from_db()

    @admin.action(description="Approve selected companies")
    def approve_companies(self, request, queryset):
        for company in queryset:
            try:
                CustomUser.objects.approve_company(company.id, admin_user=request.user)
                messages.success(request, f'Company "{company.official_name}" has been approved.')
            except ValueError as e:
                messages.error(request, f'Error approving {company.official_name}: {str(e)}')
                continue

    @admin.action(description="Reject selected companies")
    def reject_companies(self, request, queryset):
        for company in queryset:
            try:
                CustomUser.objects.reject_company(company.id)
                messages.success(request, f'Company "{company.official_name}" has been rejected.')
            except ValueError as e:
                messages.error(request, f'Error rejecting {company.official_name}: {str(e)}')
                continue
