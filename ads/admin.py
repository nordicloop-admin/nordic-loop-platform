from django.contrib import admin
from .models import Ad

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'item_name',
        'category',
        'subcategory',
        'material_frequency',
        'specification',
        'origin',
        'contamination',
        'additives',
        'storage',
        'processing_methods',
        'location',
        'delivery',
        'user',
    )
    search_fields = ('item_name', 'location', 'category__name', 'subcategory__name')
    list_filter = ('category', 'subcategory', 'material_frequency', 'origin', 'contamination', 'storage', 'delivery')
