from django.contrib import admin
from .models import Ad, Location, Address, Subscription


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'company', 
        'type', 
        'city', 
        'country', 
        'is_verified', 
        'is_primary', 
        'contact_name', 
        'created_at'
    )
    
    list_filter = (
        'type', 
        'country', 
        'is_verified', 
        'is_primary', 
        'created_at'
    )
    
    search_fields = (
        'company__official_name',
        'contact_name',
        'contact_phone',
        'address_line1',
        'address_line2',
        'city',
        'country',
        'postal_code'
    )
    
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company',)
        }),
        ('Address Details', {
            'fields': ('type', 'address_line1', 'address_line2', 'city', 'postal_code', 'country')
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'contact_phone')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_primary')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-created_at']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'company',
        'plan',
        'status',
        'start_date',
        'end_date',
        'auto_renew',
        'payment_method',
        'amount'
    )
    
    list_filter = (
        'plan',
        'status',
        'payment_method',
        'auto_renew',
        'start_date',
        'end_date'
    )
    
    search_fields = (
        'company__official_name',
        'contact_name',
        'contact_email',
        'amount'
    )
    
    readonly_fields = ('start_date',)
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company',)
        }),
        ('Subscription Details', {
            'fields': ('plan', 'status', 'start_date', 'end_date', 'auto_renew')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'last_payment', 'amount')
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'contact_email')
        }),
    )
    
    ordering = ['-start_date']


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
