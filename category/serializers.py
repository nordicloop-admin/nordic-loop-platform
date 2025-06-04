from rest_framework import serializers
from .models import Category, SubCategory, CategorySpecification



class SubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(write_only=True)

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'category_name']  # You can add more fields if needed

    def create(self, validated_data):
        category_name = validated_data.pop('category_name')
        try:
            category = Category.objects.get(name=category_name)
        except Category.DoesNotExist:
            raise serializers.ValidationError(f"Category with name '{category_name}' does not exist.")
        
        return SubCategory.objects.create(category=category, **validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['category_name'] = instance.category.name  # Include readable name
        return rep
    

    def update(self, instance, validated_data):
        if 'name' in validated_data:
            validated_data['name'] = validated_data['name'].strip().title()
        return super().update(instance, validated_data)
    


class SimpleSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['id', 'name']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SimpleSubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'subcategories']



class CategorySpecificationSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='Category.name', read_only=True)

    class Meta:
        model = CategorySpecification
        fields = [
            'id',
            'category',
            'color',
            'material_grade',
            'material_form'
        ]






