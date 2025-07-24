from rest_framework import serializers
from .models import CategorySubscription
from category.models import Category, SubCategory
from ads.models import Ad

class ConciseSubCategorySerializer(serializers.ModelSerializer):
    """
    Simplified serializer for subcategories
    """
    class Meta:
        model = SubCategory
        fields = ['id', 'name']

class ConciseCategorySerializer(serializers.ModelSerializer):
    """
    Simplified serializer for categories
    """
    class Meta:
        model = Category
        fields = ['id', 'name']

class RelatedAdSerializer(serializers.ModelSerializer):
    """
    Serializer for ads related to a category subscription
    """
    class Meta:
        model = Ad
        fields = [
            'id', 
            'title', 
            'description',
            'packaging',
            'auction_duration',
            'storage_conditions',
            'contamination',
            'available_quantity',
            'unit_of_measurement',
            'starting_bid_price',
            'currency',
            'created_at'
        ]

class CategorySubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for the CategorySubscription model with concise output
    and related auction data
    """
    material_type = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.SerializerMethodField()
    related_ads = serializers.SerializerMethodField()
    
    class Meta:
        model = CategorySubscription
        fields = [
            'id', 
            'material_type', 
            'subcategory_name',
            'created_at',
            'related_ads'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_subcategory_name(self, obj):
        if obj.subcategory:
            return obj.subcategory.name
        return None
    
    def get_related_ads(self, obj):
        # Get ads related to this subscription's category/subcategory
        ads_query = Ad.objects.filter(category=obj.category, is_active=True)
        
        # If subscription is for a specific subcategory, filter by that too
        if obj.subcategory:
            ads_query = ads_query.filter(subcategory=obj.subcategory)
            
        # Limit to 5 most recent ads to avoid overwhelming response
        ads = ads_query.order_by('-created_at')[:5]
        
        return RelatedAdSerializer(ads, many=True).data
