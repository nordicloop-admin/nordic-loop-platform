from rest_framework import serializers
from .models import Ad, Location, Subscription, Address
from category.serializers import CategorySpecificationSerializer
from category.models import Category, SubCategory, CategorySpecification
from decimal import Decimal
import decimal
from django.contrib.auth import get_user_model
from django.db.models import Max
from users.serializers import UserSerializer
from users.models import User

User = get_user_model()


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
        # Handle category change - if category changes, clear existing specifications
        category_id = validated_data.get('category_id')
        if category_id and instance.category and instance.category.id != category_id:
            # Category is changing, clear existing specifications
            if instance.specification:
                instance.specification.delete()
                instance.specification = None
        
        # Update step tracking
        validated_data['current_step'] = max(validated_data.get('current_step', 1), 2)
        return super().update(instance, validated_data)


class AdStep2Serializer(serializers.ModelSerializer):
    """Step 2: Specifications"""
    specification = CategorySpecificationSerializer(read_only=True)
    
    # Direct specification fields for easy frontend handling
    specification_color = serializers.CharField(write_only=True, required=False, allow_blank=True)
    specification_material_grade = serializers.CharField(write_only=True, required=False, allow_blank=True)
    specification_material_form = serializers.CharField(write_only=True, required=False, allow_blank=True)
    specification_additional = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Ad
        fields = [
            'id', 'specification', 'additional_specifications', 'current_step',
            'specification_color', 'specification_material_grade', 
            'specification_material_form', 'specification_additional'
        ]

    def validate_specification_color(self, value):
        if value:
            valid_colors = [choice[0] for choice in CategorySpecification.MATERIAL_COLOR_CHOICES]
            if value not in valid_colors:
                raise serializers.ValidationError(f"'{value}' is not a valid color choice.")
        return value

    def validate_specification_material_grade(self, value):
        if value:
            valid_grades = [choice[0] for choice in CategorySpecification.MATERIAL_GRADE_CHOICES]
            if value not in valid_grades:
                raise serializers.ValidationError(f"'{value}' is not a valid material grade choice.")
        return value

    def validate_specification_material_form(self, value):
        if value:
            valid_forms = [choice[0] for choice in CategorySpecification.MATERIAL_FORM_CHOICES]
            if value not in valid_forms:
                raise serializers.ValidationError(f"'{value}' is not a valid material form choice.")
        return value

    def validate(self, data):
        """Ensure at least one specification field is provided"""
        color = data.get('specification_color')
        grade = data.get('specification_material_grade')
        form = data.get('specification_material_form')
        additional = data.get('specification_additional')
        existing_additional = data.get('additional_specifications')

        # Check if at least one specification is provided
        if not any([color, grade, form, additional, existing_additional]):
            raise serializers.ValidationError(
                "At least one specification field must be provided (color, material grade, material form, or additional specifications)."
            )
        
        return data

    def update(self, instance, validated_data):
        # Handle specification creation/update
        color = validated_data.pop('specification_color', None)
        grade = validated_data.pop('specification_material_grade', None)
        form = validated_data.pop('specification_material_form', None)
        spec_additional = validated_data.pop('specification_additional', None)

        # If any specification fields are provided, create/update CategorySpecification
        if any([color, grade, form, spec_additional]):
            spec_data = {}
            if color:
                spec_data['color'] = color
            if grade:
                spec_data['material_grade'] = grade
            if form:
                spec_data['material_form'] = form
            if spec_additional:
                spec_data['additional_specifications'] = spec_additional

            if instance.specification:
                # Update existing specification
                for key, value in spec_data.items():
                    setattr(instance.specification, key, value)
                instance.specification.save()
            else:
                # Create new specification
                spec_data['Category'] = instance.category
                specification = CategorySpecification.objects.create(**spec_data)
                instance.specification = specification

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
            'id', 'location', 'location_data', 
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
            'starting_bid_price', 'currency', 'auction_duration', 'custom_auction_duration',
            'reserve_price', 'total_starting_value', 'current_step', 'allow_broker_bids'
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

    def validate_custom_auction_duration(self, value):
        if value is not None and value < 1:
            raise serializers.ValidationError("Custom auction duration must be at least 1 day.")
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
        
        # Validate custom auction duration when auction_duration is set to 0 (Custom)
        auction_duration = data.get('auction_duration')
        custom_duration = data.get('custom_auction_duration')
        
        if auction_duration == 0 and not custom_duration:
            raise serializers.ValidationError(
                "Custom auction duration is required when auction duration is set to 'Custom'."
            )
        
        if auction_duration != 0 and custom_duration:
            raise serializers.ValidationError(
                "Custom auction duration should only be provided when auction duration is set to 'Custom'."
            )
        
        return data

    def update(self, instance, validated_data):
        validated_data['current_step'] = max(validated_data.get('current_step', 7), 8)
        return super().update(instance, validated_data)


class AdStep8Serializer(serializers.ModelSerializer):
    """Step 8: Title, Description & Image"""
    # Use ImageField for file uploads, will be converted to URL in the model's pre_save
    material_image = serializers.ImageField(required=False, allow_null=True)
    
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
        if not value or len(value.strip()) < 30:
            raise serializers.ValidationError("Description must be at least 30 characters long.")
        return value.strip()
    
    def validate_material_image(self, value):
        """Validate image file"""
        if value:
            # Check file size (10MB limit)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("Image file too large. Maximum size is 10MB.")
            
            # Check content type
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Only image files are allowed.")
        
        return value

    def update(self, instance, validated_data):
        validated_data['current_step'] = 8
        validated_data['is_complete'] = True
        return super().update(instance, validated_data)


class AdCompleteSerializer(serializers.ModelSerializer):
    """Complete Ad serializer for viewing full ad details with all possible information"""
    # Location details
    location = LocationSerializer(read_only=True)
    
    # Category information
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    
    # Specification details
    specification = CategorySpecificationSerializer(read_only=True)
    
    # Company information (only name)
    company_name = serializers.CharField(source='user.company.official_name', read_only=True)
    
    # User information
    posted_by = serializers.CharField(source='user.name', read_only=True)
    
    # Calculated fields
    total_starting_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    step_completion_status = serializers.SerializerMethodField()
    
    # Choice field display values
    unit_of_measurement_display = serializers.CharField(source='get_unit_of_measurement_display', read_only=True)
    material_frequency_display = serializers.CharField(source='get_material_frequency_display', read_only=True)
    origin_display = serializers.CharField(source='get_origin_display', read_only=True)
    contamination_display = serializers.CharField(source='get_contamination_display', read_only=True)
    additives_display = serializers.CharField(source='get_additives_display', read_only=True)
    storage_conditions_display = serializers.CharField(source='get_storage_conditions_display', read_only=True)
    packaging_display = serializers.CharField(source='get_packaging_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    auction_duration_display = serializers.CharField(source='get_auction_duration_display', read_only=True)
    
    # Derived information
    time_remaining = serializers.SerializerMethodField()
    processing_methods_display = serializers.SerializerMethodField()
    delivery_options_display = serializers.SerializerMethodField()
    
    # Location summary
    location_summary = serializers.SerializerMethodField()

    class Meta:
        model = Ad
        fields = [
            # IDs and basic info
            'id', 'posted_by', 'company_name',
            
            # Step 1: Material Type
            'category_name', 'subcategory_name', 'specific_material',
            'packaging', 'packaging_display', 'material_frequency', 'material_frequency_display',
            
            # Step 2: Specifications
            'specification', 'additional_specifications',
            
            # Step 3: Material Origin
            'origin', 'origin_display',
            
            # Step 4: Contamination
            'contamination', 'contamination_display', 'additives', 'additives_display',
            'storage_conditions', 'storage_conditions_display',
            
            # Step 5: Processing Methods
            'processing_methods', 'processing_methods_display',
            
            # Step 6: Location & Logistics
            'location', 'location_summary', 
            'delivery_options', 'delivery_options_display',
            
            # Step 7: Quantity & Pricing
            'available_quantity', 'unit_of_measurement', 'unit_of_measurement_display',
            'minimum_order_quantity', 'starting_bid_price', 'currency', 'currency_display',
            'auction_duration', 'custom_auction_duration', 'auction_duration_display', 'reserve_price', 'total_starting_value',
            
            # Step 8: Title, Description & Image
            'title', 'description', 'keywords', 'material_image',
            
            # System fields
            'current_step', 'is_complete', 'status',
            'created_at', 'updated_at', 'auction_start_date', 'auction_end_date', 'allow_broker_bids',
            
            # Derived fields
            'step_completion_status', 'time_remaining'
        ]

    def get_step_completion_status(self, obj):
        return obj.get_step_completion_status()
    

    
    def get_time_remaining(self, obj):
        """Get time remaining in auction"""
        from django.utils import timezone
        now = timezone.now()
        
        if not obj.auction_end_date or obj.auction_end_date <= now:
            return None
            
        time_diff = obj.auction_end_date - now
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days, {hours} hours"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"
    
    def get_processing_methods_display(self, obj):
        """Get human-readable processing methods"""
        if not obj.processing_methods:
            return []
        
        choices_dict = dict(obj.PROCESSING_CHOICES)
        return [choices_dict.get(method, method) for method in obj.processing_methods]
    
    def get_delivery_options_display(self, obj):
        """Get human-readable delivery options"""
        if not obj.delivery_options:
            return []
        
        choices_dict = dict(obj.DELIVERY_OPTIONS)
        return [choices_dict.get(option, option) for option in obj.delivery_options]
    
    def get_location_summary(self, obj):
        """Get location summary"""
        if obj.location:
            parts = []
            if obj.location.city:
                parts.append(obj.location.city)
            if obj.location.state_province:
                parts.append(obj.location.state_province)
            if obj.location.country:
                parts.append(obj.location.country)
            return ", ".join(parts)
        return None


class AdListSerializer(serializers.ModelSerializer):
    """Serializer for listing ads (simplified)"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    location_summary = serializers.SerializerMethodField()
    total_starting_value = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()
    highest_bid_price = serializers.SerializerMethodField()
    base_price = serializers.DecimalField(source='starting_bid_price', max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Ad
        fields = [
            'id', 'title', 'category_name', 'subcategory_name',
            'available_quantity', 'unit_of_measurement', 'starting_bid_price',
            'currency', 'location_summary', 'total_starting_value',
            'material_image', 'created_at', 'is_complete', 'status',
            'allow_broker_bids', 'auction_start_date', 
            'auction_end_date', 'time_remaining', 'highest_bid_price', 'base_price'
        ]

    def get_total_starting_value(self, obj):
        """Calculate total starting value, handling null values"""
        try:
            if obj.starting_bid_price and obj.available_quantity:
                return float(obj.starting_bid_price * obj.available_quantity)
            return 0.00
        except (TypeError, ValueError, decimal.InvalidOperation):
            return 0.00

    def get_location_summary(self, obj):
        if obj.location:
            return f"{obj.location.city}, {obj.location.country}"
        return None

    def get_time_remaining(self, obj):
        """Get time remaining in auction"""
        from django.utils import timezone
        now = timezone.now()
        
        if not obj.auction_end_date or obj.auction_end_date <= now:
            return None
            
        time_diff = obj.auction_end_date - now
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        if days > 0:
            return f"{days} days, {hours} hours"
        elif hours > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{minutes} minutes"
    
    def get_highest_bid_price(self, obj):
        """Get the highest bid price if any bids exist, otherwise return None"""
        from bids.models import Bid
        try:
            # Check for highest bid first
            highest_bid = Bid.objects.filter(
                ad_id=obj.id,
                status__in=['active', 'winning', 'outbid']
            ).order_by('-bid_price_per_unit').first()
            
            if highest_bid:
                return float(highest_bid.bid_price_per_unit)
            else:
                return None
                
        except Exception:
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


class AdUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating complete ads with all fields"""
    location_data = serializers.DictField(write_only=True, required=False)
    # Use ImageField for file uploads
    material_image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Ad
        fields = [
            'id', 'category', 'subcategory', 'specific_material', 'packaging',
            'material_frequency', 'specification', 'additional_specifications',
            'origin', 'contamination', 'additives', 'storage_conditions',
            'processing_methods', 'location_data', 'delivery_options',
            'available_quantity', 'unit_of_measurement', 'minimum_order_quantity',
            'starting_bid_price', 'currency', 'auction_duration', 'custom_auction_duration', 'reserve_price',
            'title', 'description', 'keywords', 'material_image', 'allow_broker_bids'
        ]
        read_only_fields = ['id']
    
    def validate_material_image(self, value):
        """Validate image file"""
        if value:
            # Check file size (10MB limit)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("Image file too large. Maximum size is 10MB.")
            
            # Check content type
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("Only image files are allowed.")
        
        return value

    def validate(self, data):
        """Validate cross-field constraints"""
        # Validate minimum order quantity doesn't exceed available quantity
        available_qty = data.get('available_quantity', self.instance.available_quantity if self.instance else None)
        min_order_qty = data.get('minimum_order_quantity', self.instance.minimum_order_quantity if self.instance else None)
        
        if available_qty and min_order_qty and min_order_qty > available_qty:
            raise serializers.ValidationError(
                "Minimum order quantity cannot exceed available quantity."
            )
        
        # Validate reserve price is not lower than starting bid price
        starting_price = data.get('starting_bid_price', self.instance.starting_bid_price if self.instance else None)
        reserve_price = data.get('reserve_price', self.instance.reserve_price if self.instance else None)
        
        if starting_price and reserve_price and reserve_price < starting_price:
            raise serializers.ValidationError(
                "Reserve price cannot be lower than starting bid price."
            )
        
        return data

    def update(self, instance, validated_data):
        # Handle location data separately
        location_data = validated_data.pop('location_data', None)
        
        # Update the ad instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update completion status based on filled fields
        instance.current_step = self._calculate_current_step(instance)
        instance.is_complete = self._is_complete(instance)
        
        instance.save()
        
        # Handle location update
        if location_data:
            self._update_location(instance, location_data)
        
        return instance
    
    def _calculate_current_step(self, instance):
        """Calculate current step based on completed data"""
        if instance.title and instance.description:
            return 8
        elif instance.available_quantity and instance.starting_bid_price:
            return 7
        elif instance.location or instance.delivery_options:
            return 6
        elif instance.processing_methods:
            return 5
        elif instance.contamination and instance.additives and instance.storage_conditions:
            return 4
        elif instance.origin:
            return 3
        elif instance.specification or instance.additional_specifications:
            return 2
        else:
            return 1
    
    def _is_complete(self, instance):
        """Check if ad is complete based on material type pathway"""
        # Check if this is a plastic material by name (case-insensitive)
        is_plastic = False
        if instance.category:
            category_name = instance.category.name.lower()
            is_plastic = category_name in ['plastic', 'plastics']

        if is_plastic:
            # Full pathway for plastics (8 steps) - all fields required
            required_fields = [
                instance.category, instance.subcategory, instance.packaging, instance.material_frequency,  # Step 1
                (instance.specification or instance.additional_specifications),  # Step 2
                instance.origin,  # Step 3
                instance.contamination, instance.additives, instance.storage_conditions,  # Step 4
                instance.processing_methods,  # Step 5
                instance.location, instance.delivery_options,  # Step 6
                instance.available_quantity, instance.starting_bid_price, instance.currency,  # Step 7
                instance.title, instance.description  # Step 8
            ]
        else:
            # Shortened pathway for other materials (4 steps: 1, 6, 7, 8)
            required_fields = [
                instance.category, instance.subcategory, instance.packaging, instance.material_frequency,  # Step 1
                instance.location, instance.delivery_options,  # Step 6
                instance.available_quantity, instance.starting_bid_price, instance.currency,  # Step 7
                instance.title, instance.description  # Step 8
            ]

        return all(field for field in required_fields)
    
    def _update_location(self, instance, location_data):
        """Update or create location"""
        from .serializer import LocationSerializer
        
        try:
            if instance.location:
                location_serializer = LocationSerializer(instance.location, data=location_data, partial=True)
                if location_serializer.is_valid():
                    location_serializer.save()
            else:
                location_serializer = LocationSerializer(data=location_data)
                if location_serializer.is_valid():
                    instance.location = location_serializer.save()
                    instance.save()
        except Exception:
            pass  # Don't fail the entire update if location update fails


class AdminAuctionListSerializer(serializers.ModelSerializer):
    """
    Admin serializer for auction list view with specific field mapping
    """
    name = serializers.CharField(source='title', read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    basePrice = serializers.DecimalField(source='starting_bid_price', max_digits=12, decimal_places=3, read_only=True)
    highestBid = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    volume = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    countryOfOrigin = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()
    image = serializers.CharField(source='material_image', read_only=True)

    class Meta:
        model = Ad
        fields = [
            'id',
            'name',
            'category',
            'basePrice',
            'highestBid',
            'status',
            'volume',
            'seller',
            'countryOfOrigin',
            'createdAt',
            'image'
        ]

    def get_createdAt(self, obj):
        """
        Convert datetime to date string
        """
        if obj.created_at:
            return obj.created_at.date()
        return None

    def get_highestBid(self, obj):
        """
        Get the highest bid amount for this ad
        """
        try:
            # Get the highest bid amount using the prefetched bids
            if hasattr(obj, 'bids') and obj.bids.exists():
                highest_bid = obj.bids.aggregate(
                    highest=Max('bid_price_per_unit')
                )['highest']
                return float(highest_bid) if highest_bid else 0.0
            return 0.0
        except:
            return 0.0

    def get_status(self, obj):
        """
        Get status string based on ad state, prioritizing the actual status field
        """
        # Use the status field directly
        return obj.status

    def get_volume(self, obj):
        """
        Format volume as string with quantity and unit
        """
        if obj.available_quantity and obj.unit_of_measurement:
            return f"{obj.available_quantity} {obj.unit_of_measurement}"
        return ""

    def get_seller(self, obj):
        """
        Get seller name from company or user
        """
        if obj.user:
            if obj.user.company and obj.user.company.official_name:
                return obj.user.company.official_name
            elif obj.user.first_name and obj.user.last_name:
                return f"{obj.user.first_name} {obj.user.last_name}"
            else:
                return obj.user.username
        return ""

    def get_countryOfOrigin(self, obj):
        """
        Get country from location or user's company
        """
        if obj.location and obj.location.country:
            return obj.location.country
        elif obj.user and obj.user.company and obj.user.company.country:
            return obj.user.company.country
        return ""


class AdminAuctionDetailSerializer(AdminAuctionListSerializer):
    """
    Admin serializer for auction detail view - extends list serializer
    """
    description = serializers.CharField(read_only=True)
    specificMaterial = serializers.CharField(source='specific_material', read_only=True)
    reservePrice = serializers.DecimalField(source='reserve_price', max_digits=12, decimal_places=2, read_only=True)
    auctionEndDate = serializers.DateTimeField(source='auction_end_date', read_only=True)
    totalBids = serializers.SerializerMethodField()
    
    class Meta(AdminAuctionListSerializer.Meta):
        fields = AdminAuctionListSerializer.Meta.fields + [
            'description', 
            'specificMaterial', 
            'reservePrice', 
            'auctionEndDate',
            'totalBids'
        ]

    def get_totalBids(self, obj):
        """
        Get total number of bids for this ad
        """
        try:
            if hasattr(obj, 'bids'):
                return obj.bids.count()
            return 0
        except:
            return 0


class AdminAddressListSerializer(serializers.ModelSerializer):
    """
    Admin serializer for address list view with specific field mapping
    """
    companyId = serializers.CharField(source='company.id', read_only=True)
    companyName = serializers.CharField(source='company.official_name', read_only=True)
    addressLine1 = serializers.CharField(source='address_line1', read_only=True)
    addressLine2 = serializers.CharField(source='address_line2', read_only=True)
    postalCode = serializers.CharField(source='postal_code', read_only=True)
    isVerified = serializers.BooleanField(source='is_verified', read_only=True)
    isPrimary = serializers.BooleanField(source='is_primary', read_only=True)
    contactName = serializers.CharField(source='contact_name', read_only=True)
    contactPhone = serializers.CharField(source='contact_phone', read_only=True)
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = [
            'id',
            'companyId',
            'companyName',
            'type',
            'addressLine1',
            'addressLine2',
            'city',
            'postalCode',
            'country',
            'isVerified',
            'isPrimary',
            'contactName',
            'contactPhone',
            'createdAt'
        ]

    def get_createdAt(self, obj):
        """
        Convert date to string format
        """
        if obj.created_at:
            return obj.created_at.strftime('%Y-%m-%d')
        return None


class AdminAddressDetailSerializer(AdminAddressListSerializer):
    """
    Admin serializer for address detail view - extends list serializer
    """
    class Meta(AdminAddressListSerializer.Meta):
        fields = AdminAddressListSerializer.Meta.fields


class AdminSubscriptionListSerializer(serializers.ModelSerializer):
    """
    Admin serializer for subscription list view with specific field mapping
    """
    companyId = serializers.CharField(source='company.id', read_only=True)
    companyName = serializers.CharField(source='company.official_name', read_only=True)
    startDate = serializers.DateField(source='start_date', read_only=True)
    endDate = serializers.DateField(source='end_date', read_only=True)
    autoRenew = serializers.BooleanField(source='auto_renew', read_only=True)
    lastPayment = serializers.DateField(source='last_payment', read_only=True)
    contactName = serializers.CharField(source='contact_name', read_only=True)
    contactEmail = serializers.EmailField(source='contact_email', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id',
            'companyId',
            'companyName',
            'plan',
            'status',
            'startDate',
            'endDate',
            'autoRenew',
            'lastPayment',
            'amount',
            'contactName',
            'contactEmail'
        ]


class AdminSubscriptionDetailSerializer(AdminSubscriptionListSerializer):
    """
    Admin serializer for subscription detail view - extends list serializer
    """
    class Meta(AdminSubscriptionListSerializer.Meta):
        fields = AdminSubscriptionListSerializer.Meta.fields


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving the logged-in user's subscription
    """
    plan_display = serializers.CharField(source='get_plan_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True)
    auto_renew = serializers.BooleanField(read_only=True)
    last_payment = serializers.DateField(read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id',
            'plan',
            'plan_display',
            'status',
            'status_display',
            'start_date',
            'end_date',
            'auto_renew',
            'last_payment',
            'amount',
            'contact_name',
            'contact_email'
        ]


class UpdateUserSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for updating a user's subscription
    """
    class Meta:
        model = Subscription
        fields = [
            'plan',
            'auto_renew',
            'contact_name',
            'contact_email'
        ]
        
    def validate_plan(self, value):
        """Ensure plan is valid"""
        valid_plans = [choice[0] for choice in Subscription.PLAN_CHOICES]
        if value not in valid_plans:
            raise serializers.ValidationError(f"Invalid plan. Must be one of: {', '.join(valid_plans)}")
        return value


class CreateSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new subscription
    """
    class Meta:
        model = Subscription
        fields = [
            'plan',
            'status',
            'start_date',
            'end_date',
            'auto_renew',
            'last_payment',
            'amount',
            'contact_name',
            'contact_email'
        ]
        
    def validate_plan(self, value):
        """Ensure plan is valid"""
        valid_plans = [choice[0] for choice in Subscription.PLAN_CHOICES]
        if value not in valid_plans:
            raise serializers.ValidationError(f"Invalid plan. Must be one of: {', '.join(valid_plans)}")
        return value
        
    def validate_status(self, value):
        """Ensure status is valid"""
        valid_statuses = [choice[0] for choice in Subscription.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value
        
    def validate(self, data):
        """Validate the data"""
        # Ensure end_date is after start_date
        if 'start_date' in data and 'end_date' in data:
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError({"end_date": "End date must be after start date"})
                
        return data


class UserAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving the logged-in user's company addresses
    """
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    created_at = serializers.DateField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Address
        fields = [
            'id', 'type', 'type_display', 'address_line1', 'address_line2', 'city',
            'postal_code', 'country', 'is_verified', 'is_primary', 'contact_name',
            'contact_phone', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']


class CreateAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new company address
    """
    class Meta:
        model = Address
        fields = [
            'type', 'address_line1', 'address_line2', 'city', 'postal_code',
            'country', 'is_primary', 'contact_name', 'contact_phone'
        ]
        
    def validate_type(self, value):
        """Ensure address type is valid"""
        valid_types = [choice[0] for choice in Address.TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid address type. Must be one of: {', '.join(valid_types)}")
        return value


class UpdateAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an existing company address
    """
    class Meta:
        model = Address
        fields = [
            'type', 'address_line1', 'address_line2', 'city', 'postal_code',
            'country', 'is_primary', 'contact_name', 'contact_phone'
        ]
        
    def validate_type(self, value):
        """Ensure address type is valid"""
        valid_types = [choice[0] for choice in Address.TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid address type. Must be one of: {', '.join(valid_types)}")
        return value