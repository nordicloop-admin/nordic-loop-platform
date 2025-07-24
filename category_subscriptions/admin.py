from django.contrib import admin
from .models import CategorySubscription

@admin.register(CategorySubscription)
class CategorySubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'subcategory', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('user__username', 'user__email', 'category__name', 'subcategory__name')
    date_hierarchy = 'created_at'
