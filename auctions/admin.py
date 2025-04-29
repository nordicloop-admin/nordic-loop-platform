from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Category, Auction, AuctionImage, Bid


class AuctionImageInline(admin.TabularInline):
    model = AuctionImage
    extra = 1
    fields = ('image', 'is_primary', 'created_at')
    readonly_fields = ('created_at',)


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    fields = ('bidder', 'amount', 'is_winning', 'created_at')
    readonly_fields = ('bidder', 'amount', 'is_winning', 'created_at')
    can_delete = False
    max_num = 0
    ordering = ('-amount',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description', 'icon', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'current_price', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'category', 'is_featured')
    search_fields = ('title', 'description', 'seller__email', 'seller__name')
    readonly_fields = ('current_price', 'created_at', 'updated_at')
    fieldsets = (
        ('Auction Information', {
            'fields': ('title', 'description', 'seller', 'category')
        }),
        ('Material Details', {
            'fields': ('quantity', 'unit', 'location')
        }),
        ('Pricing', {
            'fields': ('starting_price', 'current_price', 'reserve_price')
        }),
        ('Timing', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('status', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [AuctionImageInline, BidInline]
    actions = ['approve_auctions', 'reject_auctions', 'cancel_auctions', 'feature_auctions', 'unfeature_auctions']

    def approve_auctions(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='active')
        self.message_user(request, f'{updated} auctions were successfully approved.')
    approve_auctions.short_description = "Approve selected auctions"

    def reject_auctions(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='draft')
        self.message_user(request, f'{updated} auctions were successfully rejected.')
    reject_auctions.short_description = "Reject selected auctions"

    def cancel_auctions(self, request, queryset):
        updated = queryset.filter(status__in=['active', 'pending']).update(status='cancelled')
        self.message_user(request, f'{updated} auctions were successfully cancelled.')
    cancel_auctions.short_description = "Cancel selected auctions"

    def feature_auctions(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} auctions were successfully featured.')
    feature_auctions.short_description = "Feature selected auctions"

    def unfeature_auctions(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} auctions were successfully unfeatured.')
    unfeature_auctions.short_description = "Unfeature selected auctions"


@admin.register(AuctionImage)
class AuctionImageAdmin(admin.ModelAdmin):
    list_display = ('auction', 'image_preview', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('auction__title',)
    readonly_fields = ('image_preview', 'created_at')

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image Preview'


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'bidder', 'amount', 'is_winning', 'created_at')
    list_filter = ('is_winning', 'created_at')
    search_fields = ('auction__title', 'bidder__email', 'bidder__name')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Bid Information', {
            'fields': ('auction', 'bidder', 'amount', 'is_winning')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


