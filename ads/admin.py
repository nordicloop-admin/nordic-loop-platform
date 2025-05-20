from django.contrib import admin
from .models import Ad

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display=('id','item_name','category','subcategory','description', 'base_price','price_per_partition', 'volume', 'selling_type', 'unit', 'country_of_origin', 'end_date', 'end_time', 'item_image')