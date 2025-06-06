from django.contrib import admin
from .models import Bid, BidHistory


class BidHistoryInline(admin.TabularInline):
    model = BidHistory
    extra = 0
    readonly_fields = ['timestamp', 'change_reason', 'previous_price', 'new_price', 'previous_volume', 'new_volume']
    can_delete = False


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'ad_title', 'bid_price_per_unit', 'volume_requested', 
        'total_bid_value', 'status', 'is_winning', 'created_at'
    ]
    list_filter = ['status', 'volume_type', 'is_auto_bid', 'created_at']
    search_fields = ['user__username', 'ad__title', 'notes']
    readonly_fields = ['total_bid_value', 'created_at', 'updated_at', 'is_winning', 'rank']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'ad', 'status')
        }),
        ('Bid Details', {
            'fields': ('bid_price_per_unit', 'volume_requested', 'volume_type', 'total_bid_value')
        }),
        ('Auto-bidding', {
            'fields': ('is_auto_bid', 'max_auto_bid_price'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'is_winning', 'rank'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [BidHistoryInline]
    
    def ad_title(self, obj):
        return obj.ad.title if obj.ad.title else f"Ad #{obj.ad.id}"
    ad_title.short_description = "Ad Title"
    
    def is_winning(self, obj):
        return obj.is_winning
    is_winning.boolean = True
    is_winning.short_description = "Winning Bid"


@admin.register(BidHistory)
class BidHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'bid', 'change_reason', 'new_price', 'new_volume', 'timestamp']
    list_filter = ['change_reason', 'timestamp']
    search_fields = ['bid__user__username', 'bid__ad__title']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Bid Information', {
            'fields': ('bid', 'change_reason')
        }),
        ('Price Changes', {
            'fields': ('previous_price', 'new_price')
        }),
        ('Volume Changes', {
            'fields': ('previous_volume', 'new_volume')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )