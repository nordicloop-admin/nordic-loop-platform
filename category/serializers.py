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
    category_name = serializers.CharField(source='Category.name', read_only=True)
    
    # Display choices for frontend
    material_grade_display = serializers.CharField(source='get_material_grade_display', read_only=True)
    material_form_display = serializers.CharField(source='get_material_form_display', read_only=True)
    color_display = serializers.CharField(source='get_color_display', read_only=True)
    
    class Meta:
        model = CategorySpecification
        fields = [
            'id',
            'Category',
            'category_name',
            'color',
            'color_display',
            'material_grade',
            'material_grade_display',
            'material_form',
            'material_form_display',
            'additional_specifications'
        ]

    def validate(self, data):
        """Ensure at least one specification field is provided"""
        color = data.get('color')
        material_grade = data.get('material_grade')
        material_form = data.get('material_form')
        additional_specs = data.get('additional_specifications')

        if not any([color, material_grade, material_form, additional_specs]):
            raise serializers.ValidationError(
                "At least one specification field (color, material grade, material form, or additional specifications) must be provided."
            )
        
        return data

    def create(self, validated_data):
        """Create a new CategorySpecification"""
        return CategorySpecification.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update existing CategorySpecification"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CategorySpecificationChoicesSerializer(serializers.Serializer):
    """Serializer to return all available choices for the frontend"""
    material_colors = serializers.SerializerMethodField()
    material_grades = serializers.SerializerMethodField()
    material_forms = serializers.SerializerMethodField()

    def get_material_colors(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in CategorySpecification.MATERIAL_COLOR_CHOICES]

    def get_material_grades(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in CategorySpecification.MATERIAL_GRADE_CHOICES]

    def get_material_forms(self, obj):
        return [{'value': choice[0], 'label': choice[1]} for choice in CategorySpecification.MATERIAL_FORM_CHOICES]






