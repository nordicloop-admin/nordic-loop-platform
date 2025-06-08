from django.contrib import admin
from .models import Category, SubCategory, CategorySpecification

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(SubCategory)  
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category']
    list_filter = ['category']
    search_fields = ['name', 'category__name']

@admin.register(CategorySpecification)
class CategorySpecificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'Category', 'material_grade', 'color', 'material_form', 'has_additional_specs']
    list_filter = ['Category', 'material_grade', 'color', 'material_form']
    search_fields = ['Category__name', 'additional_specifications']
    readonly_fields = ['id']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('Category',)
        }),
        ('Specifications', {
            'fields': ('material_grade', 'color', 'material_form'),
            'description': 'Select one or more specification options'
        }),
        ('Additional Details', {
            'fields': ('additional_specifications',),
            'classes': ('collapse',),
            'description': 'Optional: Add technical specifications like density, melt flow index, etc.'
        }),
    )
    
    def has_additional_specs(self, obj):
        """Show if additional specifications are provided"""
        return bool(obj.additional_specifications)
    has_additional_specs.boolean = True
    has_additional_specs.short_description = 'Has Additional Specs'
