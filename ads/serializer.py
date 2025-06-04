from rest_framework import serializers
from .models import Ad
from category.serializers import CategorySpecificationSerializer

class AdStep1Serializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    subcategory = serializers.CharField(source='subcategory.name', read_only=True)

    class Meta:
        model = Ad
        fields = ['id', 'item_name', 'category', 'subcategory', 'material_frequency']



class AdStep2Serializer(serializers.ModelSerializer):
    specification = CategorySpecificationSerializer(read_only=True)

    class Meta:
        model = Ad
        fields = ['id', 'specification']


class AdStep3Serializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ['id', 'origin']


class AdStep4Serializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ['id', 'contamination', 'additives', 'storage']


class AdStep5Serializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ['id', 'processing_methods']
    

class AdStep6Serializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ['id', 'location', 'delivery']




     