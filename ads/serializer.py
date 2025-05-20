from rest_framework import serializers
from .models import Ad

class AdSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    subcategory = serializers.CharField(source='subcategory.name', read_only=True)

    class Meta:
        model = Ad
        fields = [
            'id',
            'item_name',
            'category',
            'subcategory',
            'description',
            'base_price',
            'price_per_partition',
            'volume',
            'unit',
            'selling_type',
            'country_of_origin',
            'end_date',
            'end_time',
            'item_image',
        ]
