from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Bid, BidHistory
from ads.models import Ad
from users.serializers import UserSerializer

User = get_user_model()


class BidSerializer(serializers.ModelSerializer):
    """Legacy serializer - updated for new fields"""
    user = serializers.SlugRelatedField(read_only=True, slug_field='username')
    ad_title = serializers.CharField(source='ad.title', read_only=True)
    currency = serializers.CharField(source='ad.currency', read_only=True)

    class Meta:
        model = Bid
        fields = [
            'id', 'user', 'ad', 'ad_title', 'bid_price_per_unit', 'volume_requested',
            'total_bid_value', 'currency', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'total_bid_value']


class BidCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new bids"""
    
    class Meta:
        model = Bid
        fields = [
            'ad', 'bid_price_per_unit', 'volume_requested', 
            'volume_type', 'notes', 'max_auto_bid_price', 'is_auto_bid'
        ]
        
    def validate_ad(self, value):
        """Validate that the ad exists and is active"""
        if not value.is_active or not value.is_complete:
            raise serializers.ValidationError("Cannot bid on inactive or incomplete ads.")
        return value

    def validate(self, attrs):
        """Custom validation for broker permissions"""
        user = self.context['request'].user if 'request' in self.context else None
        ad = attrs.get('ad')

        if user and ad:
            # Check broker bid permissions
            if (user.company and
                user.company.sector == 'broker' and
                not ad.allow_broker_bids):
                raise serializers.ValidationError(
                    "This company has chosen not to sell this material to brokers."
                )

        return super().validate(attrs)
    
    def validate_bid_price_per_unit(self, value):
        """Validate bid price"""
        if value <= 0:
            raise serializers.ValidationError("Bid price must be greater than zero.")
        return value
    
    def validate_volume_requested(self, value):
        """Validate volume requested"""
        if value <= 0:
            raise serializers.ValidationError("Volume requested must be greater than zero.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        ad = data.get('ad')
        volume_requested = data.get('volume_requested')
        bid_price = data.get('bid_price_per_unit')
        
        if ad and volume_requested:
            # Check if volume requested doesn't exceed available quantity
            if volume_requested > ad.available_quantity:
                raise serializers.ValidationError(
                    f"Volume requested ({volume_requested}) cannot exceed available quantity ({ad.available_quantity})."
                )
            
            # Check minimum order quantity
            if ad.minimum_order_quantity and volume_requested < ad.minimum_order_quantity:
                raise serializers.ValidationError(
                    f"Volume requested ({volume_requested}) is below minimum order quantity ({ad.minimum_order_quantity})."
                )
        
        if ad and bid_price:
            # Check if bid meets minimum starting price
            if bid_price < ad.starting_bid_price:
                raise serializers.ValidationError(
                    f"Bid price ({bid_price}) must be at least the starting bid price ({ad.starting_bid_price})."
                )
        
        return data
    
    def create(self, validated_data):
        """Create bid with automatic user assignment or update existing bid"""
        # Get user from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user

        user = validated_data['user']
        ad = validated_data['ad']
        new_bid_price = validated_data['bid_price_per_unit']

        # Check if user already has a bid for this ad
        existing_bid = Bid.objects.filter(user=user, ad=ad).first()

        if existing_bid:
            # Validate that new bid amount is not lower than previous bid
            if new_bid_price < existing_bid.bid_price_per_unit:
                raise serializers.ValidationError({
                    'bid_price_per_unit': f"New bid amount ({new_bid_price}) cannot be lower than your previous bid ({existing_bid.bid_price_per_unit})"
                })

            # Store previous values for history tracking
            previous_price = existing_bid.bid_price_per_unit
            previous_volume = existing_bid.volume_requested

            # Create bid history entry BEFORE updating the bid
            # This preserves the current state before the change
            from .models import BidHistory
            BidHistory.objects.create(
                bid=existing_bid,
                previous_price=previous_price,
                new_price=validated_data['bid_price_per_unit'],
                previous_volume=previous_volume,
                new_volume=validated_data['volume_requested'],
                change_reason='bid_updated'
            )

            # Update existing bid with new values
            for field, value in validated_data.items():
                if field != 'user':  # Don't update user field
                    setattr(existing_bid, field, value)

            # Calculate total bid value
            existing_bid.total_bid_value = (
                existing_bid.bid_price_per_unit * existing_bid.volume_requested
            )

            # Save the updated bid
            existing_bid.save()

            return existing_bid
        else:
            # Calculate total bid value for new bid
            validated_data['total_bid_value'] = (
                validated_data['bid_price_per_unit'] * validated_data['volume_requested']
            )

            # Create new bid
            new_bid = super().create(validated_data)

            # Create bid history entry for the initial bid
            from .models import BidHistory
            BidHistory.objects.create(
                bid=new_bid,
                previous_price=None,  # No previous price for new bids
                new_price=new_bid.bid_price_per_unit,
                previous_volume=None,  # No previous volume for new bids
                new_volume=new_bid.volume_requested,
                change_reason='bid_placed'
            )

            return new_bid


class AdBasicSerializer(serializers.ModelSerializer):
    """Basic ad info for bid serialization"""
    seller_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Ad
        fields = [
            'id', 'title', 'category', 'available_quantity', 'unit_of_measurement',
            'starting_bid_price', 'currency', 'auction_end_date', 'seller_name'
        ]


class BidListSerializer(serializers.ModelSerializer):
    """Serializer for listing bids (simplified view)"""
    ad_title = serializers.CharField(source='ad.title', read_only=True)
    ad_id = serializers.IntegerField(source='ad.id', read_only=True)
    bidder_name = serializers.CharField(source='user.username', read_only=True)
    company_name = serializers.CharField(source='user.company.official_name', read_only=True)

    class Meta:
        model = Bid
        fields = [
            'id', 'ad_id', 'ad_title', 'bidder_name', 'company_name',
            'bid_price_per_unit', 'volume_requested', 'total_bid_value',
            'status', 'created_at', 'updated_at'
        ]


class WinningBidSerializer(serializers.ModelSerializer):
    """Enhanced serializer for winning bids with additional auction and seller details"""
    ad_title = serializers.CharField(source='ad.title', read_only=True)
    ad_id = serializers.IntegerField(source='ad.id', read_only=True)
    bidder_name = serializers.CharField(source='user.username', read_only=True)
    company_name = serializers.CharField(source='user.company.official_name', read_only=True)

    # Additional fields for winning bids
    ad_category = serializers.CharField(source='ad.category.name', read_only=True)
    ad_user_email = serializers.CharField(source='ad.user.email', read_only=True)
    ad_location = serializers.SerializerMethodField()
    currency = serializers.CharField(source='ad.currency', read_only=True)
    unit = serializers.CharField(source='ad.unit_of_measurement', read_only=True)

    class Meta:
        model = Bid
        fields = [
            'id', 'ad_id', 'ad_title', 'bidder_name', 'company_name',
            'bid_price_per_unit', 'volume_requested', 'total_bid_value',
            'status', 'created_at', 'updated_at',
            # Additional fields for winning bids
            'ad_category', 'ad_user_email', 'ad_location', 'currency', 'unit'
        ]

    def get_ad_location(self, obj):
        """Get formatted location string"""
        if obj.ad.location:
            location_parts = []
            if obj.ad.location.city:
                location_parts.append(obj.ad.location.city)
            if obj.ad.location.country:
                location_parts.append(obj.ad.location.country)
            return ', '.join(location_parts) if location_parts else None
        return None


class BidDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed bid view"""
    ad_details = serializers.SerializerMethodField()
    bidder_details = serializers.SerializerMethodField()
    bid_ranking = serializers.SerializerMethodField()
    
    class Meta:
        model = Bid
        fields = [
            'id', 'ad_details', 'bidder_details', 'bid_price_per_unit',
            'volume_requested', 'total_bid_value', 'notes', 'status', 
            'created_at', 'updated_at', 'bid_ranking'
        ]
    
    def get_ad_details(self, obj):
        """Get relevant ad information"""
        return {
            'id': obj.ad.id,
            'title': obj.ad.title,
            'starting_bid_price': obj.ad.starting_bid_price,
            'available_quantity': obj.ad.available_quantity,
            'minimum_order_quantity': obj.ad.minimum_order_quantity,
            'currency': obj.ad.currency,
            'auction_end_date': obj.ad.auction_end_date
        }
    
    def get_bidder_details(self, obj):
        """Get bidder information"""
        return {
            'username': obj.user.username,
            'company': obj.user.company.official_name if obj.user.company else None,
            'email': obj.user.email
        }
    
    def get_bid_ranking(self, obj):
        """Get bid ranking among all bids for this ad"""
        higher_bids = Bid.objects.filter(
            ad=obj.ad,
            bid_price_per_unit__gt=obj.bid_price_per_unit,
            status__in=['active', 'winning']
        ).count()
        return higher_bids + 1


class BidUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing bids"""
    
    class Meta:
        model = Bid
        fields = [
            'bid_price_per_unit', 'volume_requested', 
            'volume_type', 'notes', 'max_auto_bid_price', 'is_auto_bid'
        ]
    
    def validate_bid_price_per_unit(self, value):
        """Validate bid price"""
        if value <= 0:
            raise serializers.ValidationError("Bid price must be greater than zero.")
        return value
    
    def validate_volume_requested(self, value):
        """Validate volume requested"""
        if value <= 0:
            raise serializers.ValidationError("Volume requested must be greater than zero.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        instance = self.instance
        ad = instance.ad
        
        volume_requested = data.get('volume_requested', instance.volume_requested)
        bid_price = data.get('bid_price_per_unit', instance.bid_price_per_unit)
        
        # Check if volume requested doesn't exceed available quantity
        if volume_requested > ad.available_quantity:
            raise serializers.ValidationError(
                f"Volume requested ({volume_requested}) cannot exceed available quantity ({ad.available_quantity})."
            )
        
        # Check minimum order quantity
        if ad.minimum_order_quantity and volume_requested < ad.minimum_order_quantity:
            raise serializers.ValidationError(
                f"Volume requested ({volume_requested}) is below minimum order quantity ({ad.minimum_order_quantity})."
            )
        
        # Check if bid meets minimum starting price
        if bid_price < ad.starting_bid_price:
            raise serializers.ValidationError(
                f"Bid price ({bid_price}) must be at least the starting bid price ({ad.starting_bid_price})."
            )
        
        return data
    
    def update(self, instance, validated_data):
        """Update bid with total bid value recalculation and history tracking"""

        # Store previous values for history tracking
        previous_price = instance.bid_price_per_unit
        previous_volume = instance.volume_requested

        # Calculate new total bid value if price or volume changes
        if 'bid_price_per_unit' in validated_data or 'volume_requested' in validated_data:
            bid_price = validated_data.get('bid_price_per_unit', instance.bid_price_per_unit)
            volume = validated_data.get('volume_requested', instance.volume_requested)
            validated_data['total_bid_value'] = bid_price * volume

            # Create bid history entry BEFORE updating the bid
            # Only create history if price or volume actually changed
            if (bid_price != previous_price or volume != previous_volume):
                from .models import BidHistory
                BidHistory.objects.create(
                    bid=instance,
                    previous_price=previous_price,
                    new_price=bid_price,
                    previous_volume=previous_volume,
                    new_volume=volume,
                    change_reason='bid_updated'
                )

        return super().update(instance, validated_data)


class BidHistorySerializer(serializers.ModelSerializer):
    """Serializer for bid history"""

    class Meta:
        model = BidHistory
        fields = ['id', 'bid', 'previous_price', 'new_price', 'previous_volume', 'new_volume', 'change_reason', 'timestamp']


class BidStatsSerializer(serializers.Serializer):
    """Serializer for bid statistics"""
    total_bids = serializers.IntegerField()
    highest_bid = serializers.DecimalField(max_digits=15, decimal_places=3)
    lowest_bid = serializers.DecimalField(max_digits=15, decimal_places=3)
    average_bid = serializers.DecimalField(max_digits=15, decimal_places=3)
    total_volume_requested = serializers.DecimalField(max_digits=15, decimal_places=3)
    unique_bidders = serializers.IntegerField()
    bid_range = serializers.DecimalField(max_digits=15, decimal_places=3)
    
    # Status breakdown
    active_bids = serializers.IntegerField()
    winning_bids = serializers.IntegerField()
    outbid_bids = serializers.IntegerField()
    rejected_bids = serializers.IntegerField()


class AdminBidListSerializer(serializers.ModelSerializer):
    """
    Admin serializer for bid list view with specific field mapping
    """
    itemId = serializers.IntegerField(source='ad.id', read_only=True)
    itemName = serializers.CharField(source='ad.title', read_only=True)
    bidderName = serializers.SerializerMethodField()
    bidderEmail = serializers.CharField(source='user.email', read_only=True)
    bidAmount = serializers.DecimalField(source='bid_price_per_unit', max_digits=12, decimal_places=3, read_only=True)
    volume = serializers.DecimalField(source='volume_requested', max_digits=10, decimal_places=3, read_only=True)
    unit = serializers.CharField(source='ad.unit_of_measurement', read_only=True)
    bidDate = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Bid
        fields = [
            'id',
            'itemId',
            'itemName',
            'bidderName',
            'bidderEmail',
            'bidAmount',
            'volume',
            'unit',
            'status',
            'bidDate'
        ]

    def get_bidderName(self, obj):
        """
        Get bidder name from user's first_name, last_name, or username
        """
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        elif obj.user.name:
            return obj.user.name
        else:
            return obj.user.username


class AdminBidDetailSerializer(AdminBidListSerializer):
    """
    Admin serializer for bid detail view - extends list serializer
    """
    # Add any additional fields for detail view if needed
    totalValue = serializers.DecimalField(source='total_bid_value', max_digits=15, decimal_places=2, read_only=True)
    notes = serializers.CharField(read_only=True)
    companyName = serializers.CharField(source='user.company.official_name', read_only=True)
    
    class Meta(AdminBidListSerializer.Meta):
        fields = AdminBidListSerializer.Meta.fields + ['totalValue', 'notes', 'companyName']
