from django.contrib import admin
from company.models import Company

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        'official_name', 'vat_number', 'email', 'country', 'status', 'registration_date', 'get_contacts_count'
    )
    list_filter = ('status', 'registration_date', 'sector')
    search_fields = (
        'official_name', 'vat_number', 'email'
    )

    fieldsets = (
        ('Company Information', {
            'fields': ('official_name', 'vat_number', 'email', 'country', 'sector', 'website', 'status')
        }),
        ('Contact Information', {
            'description': 'Contact persons are managed through the User model. Use the Users admin to manage company contacts.',
            'fields': (),
        }),
    )

    readonly_fields = ('registration_date',)

    def get_contacts_count(self, obj):
        """Display number of contact users for this company"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        count = User.objects.filter(
            company=obj,
            contact_type__in=['primary', 'secondary']
        ).count()
        return f"{count} contacts"
    get_contacts_count.short_description = 'Contacts'
