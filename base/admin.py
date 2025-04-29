from django.contrib import admin
from base.models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'street_number', 'city', 'country', 'created_at')
    search_fields = ('street_number', 'city', 'country', 'province', 'district')
    list_filter = ('country', 'province', 'city')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Location', {
            'fields': ('country', 'province', 'district', 'city', 'street_number', 'code')
        }),
        ('Additional Information', {
            'fields': ('additional_info',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'is_active', 'is_deleted')
        }),
    )
