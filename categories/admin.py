from django.contrib import admin
from django.utils.html import format_html
from .models import Category


class CategoryInline(admin.TabularInline):
    model = Category
    extra = 1
    fields = ('name', 'slug', 'is_active')
    show_change_link = True
    verbose_name = "Subcategory"
    verbose_name_plural = "Subcategories"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('indented_name', 'slug', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CategoryInline]

    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'slug', 'description', 'parent', 'is_active', 'icon')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def indented_name(self, obj):
        """Display the category name with indentation based on hierarchy level"""
        level = obj.get_hierarchy_level()
        indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * level
        if level > 0:
            return format_html('{}<span style="color: #555;">└─</span> {}', indent, obj.name)
        return obj.name
    indented_name.short_description = 'Name'
    indented_name.admin_order_field = 'name'

    def get_queryset(self, request):
        """Optimize the queryset to reduce database queries"""
        return super().get_queryset(request).select_related('parent')
