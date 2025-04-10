from django.contrib import admin
from django.contrib import messages
from .models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('official_name', 'vat_number', 'email', 'status', 'registration_date')
    list_filter = ('status', 'registration_date')
    search_fields = ('official_name', 'vat_number', 'email')
    readonly_fields = ('registration_date', 'approval_date', 'user')
    
    fieldsets = (
        ('Company Information', {
            'fields': ('official_name', 'vat_number', 'email', 'business_address', 
                      'phone_number', 'website')
        }),
        ('Status', {
            'fields': ('status', 'registration_date', 'approval_date', 'rejection_reason')
        }),
        ('User Account', {
            'fields': ('user',)
        }),
    )

    actions = ['approve_companies', 'reject_companies']

    def save_model(self, request, obj, form, change):
        try:
            if change and 'status' in form.changed_data:
                if obj.status == 'approved':
                    obj.approve(admin_user=request.user)
                    messages.success(request, f'Company "{obj.official_name}" has been approved.')
                elif obj.status == 'rejected':
                    obj.reject(reason=obj.rejection_reason)
                    messages.success(request, f'Company "{obj.official_name}" has been rejected.')
            super().save_model(request, obj, form, change)
        except ValueError as e:
            messages.error(request, str(e))
            obj.refresh_from_db()

    @admin.action(description="Approve selected companies")
    def approve_companies(self, request, queryset):
        for company in queryset:
            try:
                company.approve(admin_user=request.user)
            except ValueError as e:
                messages.error(request, f'Error approving {company.official_name}: {str(e)}')
                continue
        messages.success(request, f'{queryset.count()} companies were successfully approved.')

    @admin.action(description="Reject selected companies")
    def reject_companies(self, request, queryset):
        for company in queryset:
            try:
                company.reject()
            except ValueError as e:
                messages.error(request, f'Error rejecting {company.official_name}: {str(e)}')
                continue
        messages.success(request, f'{queryset.count()} companies were successfully rejected.')
