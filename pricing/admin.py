from django.contrib import admin
from .models import PricingPlan, BaseFeature, PlanFeature, PricingPageContent


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1
    fields = ['base_feature', 'is_included', 'feature_value', 'custom_description', 'order', 'is_highlighted']
    ordering = ['order']
    autocomplete_fields = ['base_feature']


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'currency', 'is_popular', 'is_active', 'order']
    list_filter = ['plan_type', 'is_popular', 'is_active']
    list_editable = ['price', 'is_popular', 'is_active', 'order']
    search_fields = ['name', 'plan_type']
    ordering = ['order', 'price']
    
    inlines = [PlanFeatureInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'plan_type', 'price', 'currency')
        }),
        ('Display Settings', {
            'fields': ('color', 'is_popular', 'order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(BaseFeature)
class BaseFeatureAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'base_description_short', 'is_active', 'order']
    list_filter = ['category', 'is_active']
    list_editable = ['is_active', 'order']
    search_fields = ['name', 'base_description']
    ordering = ['category', 'order']

    def base_description_short(self, obj):
        return obj.base_description[:50] + "..." if len(obj.base_description) > 50 else obj.base_description
    base_description_short.short_description = 'Description'


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    list_display = ['plan', 'base_feature', 'feature_value', 'is_included', 'is_highlighted', 'order']
    list_filter = ['plan', 'base_feature__category', 'is_included', 'is_highlighted']
    list_editable = ['feature_value', 'is_included', 'is_highlighted', 'order']
    search_fields = ['base_feature__name', 'plan__name', 'custom_description']
    ordering = ['plan__order', 'order']
    autocomplete_fields = ['base_feature']


@admin.register(PricingPageContent)
class PricingPageContentAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'section_label', 'cta_text', 'updated_at']
    
    fieldsets = (
        ('Page Header', {
            'fields': ('section_label', 'title', 'subtitle')
        }),
        ('Call to Action', {
            'fields': ('cta_text', 'cta_url')
        }),
    )
    
    def title_short(self, obj):
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title
    title_short.short_description = 'Title'
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not PricingPageContent.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion if it's the only instance
        return PricingPageContent.objects.count() > 1
