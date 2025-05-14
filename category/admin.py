from django.contrib import admin
from .models import Category, SubCategory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',) # Added a comma to make it a tuple

@admin.register(SubCategory) # Corrected to SubCategory
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'name')
