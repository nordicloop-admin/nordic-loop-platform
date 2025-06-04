from django.contrib import admin
from .models import Ad, Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'state_province', 'country', 'postal_code')
    search_fields = ('city', 'state_province', 'country', 'postal_code')
    list_filter = ('country', 'state_province')


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'category',
        'subcategory',
        'packaging',
        'material_frequency',
        'origin',
        'contamination',
        'storage_conditions',
        'available_quantity',
        'starting_bid_price',
        'currency',
        'current_step',
        'is_complete',
        'is_active',
        'user',
    )
    
    search_fields = (
        'title', 
        'description', 
        'keywords',
        'category__name', 
        'subcategory__name',
        'location__city',
        'location__country'
    )
    
    list_filter = (
        'category', 
        'subcategory', 
        'packaging',
        'material_frequency', 
        'origin', 
        'contamination',
        'storage_conditions',
        'currency',
        'current_step',
        'is_complete',
        'is_active',
        'created_at'
    )
    
    readonly_fields = ('created_at', 'updated_at', 'total_starting_value')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'keywords', 'material_image')
        }),
        ('Material Type (Step 1)', {
            'fields': ('category', 'subcategory', 'specific_material', 'packaging', 'material_frequency')
        }),
        ('Specifications (Step 2)', {
            'fields': ('specification', 'additional_specifications')
        }),
        ('Material Origin (Step 3)', {
            'fields': ('origin',)
        }),
        ('Contamination (Step 4)', {
            'fields': ('contamination', 'additives', 'storage_conditions')
        }),
        ('Processing Methods (Step 5)', {
            'fields': ('processing_methods',)
        }),
        ('Location & Logistics (Step 6)', {
            'fields': ('location', 'pickup_available', 'delivery_options')
        }),
        ('Quantity & Pricing (Step 7)', {
            'fields': (
                'available_quantity', 'unit_of_measurement', 'minimum_order_quantity',
                'starting_bid_price', 'currency', 'auction_duration', 'reserve_price'
            )
        }),
        ('System Fields', {
            'fields': (
                'current_step', 'is_complete', 'is_active',
                'auction_start_date', 'auction_end_date',
                'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['created_at', 'updated_at'])
        return readonly
