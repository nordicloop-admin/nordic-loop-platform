from django.contrib import admin
from company.models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'official_name', 'vat_number', 'email', 'country', 'status', 'registration_date'
    )
    list_filter = ('status', 'registration_date', 'sector')
    search_fields = (
        'official_name', 'vat_number', 'email',
        'primary_email', 'secondary_email'
    )

    fieldsets = (
        ('Company Information', {
            'fields': ('official_name', 'vat_number', 'sector', 'website', 'status')
        }),
        ('Primary Contact', {
            'fields': (
                'primary_first_name', 'primary_last_name',
                'primary_email', 'primary_position'
            )
        }),
        ('Secondary Contact (optional)', {
            'fields': (
                'secondary_first_name', 'secondary_last_name',
                'secondary_email', 'secondary_position'
            )
        }),
        ('Registration Credentials', {
            'fields': ('email',)
        }),
    )
