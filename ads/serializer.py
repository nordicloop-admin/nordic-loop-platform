from rest_framework import serializers
from .models import Ad, Location
from category.serializers import CategorySpecificationSerializer
from category.models import Category, SubCategory, CategorySpecification
from decimal import Decimal


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            'id', 'country', 'state_province', 'city', 
            'address_line', 'postal_code', 'latitude', 'longitude'
        ]
        
    def validate_country(self, value):
        """Ensure country is provided"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("Country is required.")
        return value.strip().title()
    
    def validate_city(self, value):
        """Ensure city is provided"""
        if not value or value.strip() == '':
            raise serializers.ValidationError("City is required.")
        return value.strip().title()


class AdStep1Serializer(serializers.ModelSerializer):
    """Step 1: Material Type"""
    category_id = serializers.IntegerField(write_only=True)
    subcategory_id = serializers.IntegerField(write_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)

    class Meta:
        model = Ad
        fields = [
            'id', 'category_id', 'subcategory_id', 'category_name', 'subcategory_name',
            'specific_material', 'packaging', 'material_frequency', 'current_step'
        ]

    def validate_category_id(self, value):
        try:
            Category.objects.get(id=value)
        except Category.DoesNotExist:
            raise serializers.ValidationError("Invalid category.")
        return value

    def validate_subcategory_id(self, value):
        try:
            SubCategory.objects.get(id=value)
        except SubCategory.DoesNotExist:
            raise serializers.ValidationError("Invalid subcategory.")
        return value

    def validate(self, data):
        """Ensure subcategory belongs to the selected category"""
        if 'category_id' in data and 'subcategory_id' in data:
            try:
                subcategory = SubCategory.objects.get(id=data['subcategory_id'])
                if subcategory.category.id != data['category_id']:
                    raise serializers.ValidationError("Subcategory must belong to the selected category.")
            except SubCategory.DoesNotExist:
                pass  # Will be caught by individual field validation
        return data

    def update(self, instance, validated_data):
        # Update step tracking
        validated_data['current_step'] = max(validated_data.get('current_step', 1), 2)
        return super().update(instance, validated_data)


class AdStep2Serializer(serializers.ModelSerializer):
    """Step 2: Specifications"""
    specification = CategorySpecificationSerializer(read_only=True)
    specification_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Ad
        fields = ['id', 'specification', 'specification_id', 'additional_specifications', 'current_step']

    def validate_specification_id(self, value):
        if value is not None:
            try:
                CategorySpecification.objects.get(id=value)
            except CategorySpecification.DoesNotExist:
                raise serializers.ValidationError("Invalid specification.")
        return value

    def update(self, instance, validated_data):
        validated_data['current_step'] = max(validated_data.get('current_step', 2), 3)
        return super().update(instance, validated_data)


class AdStep3Serializer(serializers.ModelSerializer):
    """Step 3: Material Origin"""
    class Meta:
        model = Ad
        fields = ['id', 'origin', 'current_step']

    def validate_origin(self, value):
        if not value:
            raise serializers.ValidationError("Material origin is required.")
        return value

    def update(self, instance, validated_data):
        validated_data['current_step'] = max(validated_data.get('current_step', 3), 4)
        return super().update(instance, validated_data)


class AdStep4Serializer(serializers.ModelSerializer):
    """Step 4: Contamination"""
    class Meta:
        model = Ad
        fields = ['id', 'contamination', 'additives', 'storage_conditions', 'current_step']

    def validate(self, data):
        required_fields = ['contamination', 'additives', 'storage_conditions']
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError(f"{field.replace('_', ' ').title()} is required.")
        return data

    def update(self, instance, validated_data):
        validated_data['current_step'] = max(validated_data.get('current_step', 4), 5)
        return super().update(instance, validated_data)


class AdStep5Serializer(serializers.ModelSerializer):
    """Step 5: Processing Methods"""
    class Meta:
        model = Ad
        fields = ['id', 'processing_methods', 'current_step']

    def validate_processing_methods(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one processing method must be selected.")
        
        # Validate that all processing methods are valid choices
        valid_choices = [choice[0] for choice in Ad.PROCESSING_CHOICES]
        for method in value:
            if method not in valid_choices:
                raise serializers.ValidationError(f"'{method}' is not a valid processing method.")
        return value

    def update(self, instance, validated_data):
        validated_data['current_step'] = max(validated_data.get('current_step', 5), 6)
        return super().update(instance, validated_data)


class AdStep6Serializer(serializers.ModelSerializer):
    """Step 6: Location & Logistics"""
    location = LocationSerializer(read_only=True)
    location_data = LocationSerializer(write_only=True, required=False)

    class Meta:
        model = Ad
        fields = [
            'id', 'location', 'location_data', 'pickup_available', 
            'delivery_options', 'current_step'
        ]

    def validate_delivery_options(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one delivery option must be selected.")
        
        # Validate that all delivery options are valid choices
        valid_choices = [choice[0] for choice in Ad.DELIVERY_OPTIONS]
        for option in value:
            if option not in valid_choices:
                raise serializers.ValidationError(f"'{option}' is not a valid delivery option.")
        return value

    def update(self, instance, validated_data):
        # Handle location creation/update
        location_data = validated_data.pop('location_data', None)
        if location_data:
            if instance.location:
                # Update existing location
                location_serializer = LocationSerializer(instance.location, data=location_data, partial=True)
                if location_serializer.is_valid(raise_exception=True):
                    location_serializer.save()
            else:
                # Create new location
                location_serializer = LocationSerializer(data=location_data)
                if location_serializer.is_valid(raise_exception=True):
                    instance.location = location_serializer.save()

        validated_data['current_step'] = max(validated_data.get('current_step', 6), 7)
        return super().update(instance, validated_data)


class AdStep7Serializer(serializers.ModelSerializer):
    """Step 7: Quantity & Pricing"""
    total_starting_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Ad
        fields = [
            'id', 'available_quantity', 'unit_of_measurement', 'minimum_order_quantity',
            'starting_bid_price', 'currency', 'auction_duration', 'reserve_price',
            'total_starting_value', 'current_step'
        ]

    def validate_available_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Available quantity must be greater than 0.")
        return value

    def validate_starting_bid_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Starting bid price must be greater than 0.")
        return value

    def validate_reserve_price(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("Reserve price must be greater than 0.")
        return value

    def validate(self, data):
        # Validate minimum order quantity doesn't exceed available quantity
        available_qty = data.get('available_quantity')
        min_order_qty = data.get('minimum_order_quantity', 0)
        
        if available_qty and min_order_qty and min_order_qty > available_qty:
            raise serializers.ValidationError(
                "Minimum order quantity cannot exceed available quantity."
            )
        
        # Validate reserve price is not lower than starting bid price
        starting_price = data.get('starting_bid_price')
        reserve_price = data.get('reserve_price')
        
        if starting_price and reserve_price and reserve_price < starting_price:
            raise serializers.ValidationError(
                "Reserve price cannot be lower than starting bid price."
            )
        
        return data

    def update(self, instance, validated_data):
        validated_data['current_step'] = max(validated_data.get('current_step', 7), 8)
        return super().update(instance, validated_data)


class AdStep8Serializer(serializers.ModelSerializer):
    """Step 8: Title, Description & Image"""
    class Meta:
        model = Ad
        fields = [
            'id', 'title', 'description', 'keywords', 
            'material_image', 'current_step', 'is_complete'
        ]

    def validate_title(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Title must be at least 10 characters long.")
        return value.strip()

    def validate_description(self, value):
        if not value or len(value.strip()) < 50:
            raise serializers.ValidationError("Description must be at least 50 characters long.")
        return value.strip()

    def update(self, instance, validated_data):
        validated_data['current_step'] = 8
        validated_data['is_complete'] = True
        return super().update(instance, validated_data)


class AdCompleteSerializer(serializers.ModelSerializer):
    """Complete Ad serializer for viewing full ad details"""
    location = LocationSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    specification = CategorySpecificationSerializer(read_only=True)
    total_starting_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    step_completion_status = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = [
            'id', 'user', 'category_name', 'subcategory_name', 'specific_material',
            'packaging', 'material_frequency', 'specification', 'additional_specifications',
            'origin', 'contamination', 'additives', 'storage_conditions',
            'processing_methods', 'location', 'pickup_available', 'delivery_options',
            'available_quantity', 'unit_of_measurement', 'minimum_order_quantity',
            'starting_bid_price', 'currency', 'auction_duration', 'reserve_price',
            'total_starting_value', 'title', 'description', 'keywords',
            'material_image', 'is_active', 'current_step', 'is_complete',
            'created_at', 'updated_at', 'auction_start_date', 'auction_end_date',
            'step_completion_status'
        ]

    def get_step_completion_status(self, obj):
        return obj.get_step_completion_status()


class AdListSerializer(serializers.ModelSerializer):
    """Serializer for listing ads (simplified)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    location_summary = serializers.SerializerMethodField()
    total_starting_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Ad
        fields = [
            'id', 'title', 'category_name', 'subcategory_name',
            'available_quantity', 'unit_of_measurement', 'starting_bid_price',
            'currency', 'location_summary', 'total_starting_value',
            'material_image', 'created_at', 'is_active', 'is_complete'
        ]

    def get_location_summary(self, obj):
        if obj.location:
            return f"{obj.location.city}, {obj.location.country}"
        return None


class AdCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new ad (minimal initial data)"""
    class Meta:
        model = Ad
        fields = ['id', 'user', 'current_step']
        read_only_fields = ['id', 'current_step']

    def create(self, validated_data):
        validated_data['current_step'] = 1
        validated_data['is_complete'] = False
        return super().create(validated_data)




     