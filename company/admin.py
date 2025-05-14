from django.contrib import admin
from company.models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('official_name', 'vat_number', 'email', 'country','status', 'registration_date')
    list_filter = ('status', 'registration_date', 'sector')
    search_fields = ('official_name', 'vat_number', 'email', 'contact_email')
    

    fieldsets = (
    ('Company Information', {
        'fields': ('official_name', 'vat_number', 'sector', 'website', 'status')
    }),
    ('Contact Information', {
        'fields': ('contact_name', 'contact_position', 'contact_email')
    }),
    ('Registration Credentials', {
        'fields': ('email',)
    }),
)