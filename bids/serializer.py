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
            'delivery_requirements', 'payment_terms', 'notes'
        ]
        
    def validate_ad(self, value):
        """Validate that the ad exists and is active"""
        if not value.is_active or not value.is_complete:
            raise serializers.ValidationError("Cannot bid on inactive or incomplete ads.")
        return value
    
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
        """Create bid with automatic user assignment"""
        # Get user from request context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        # Calculate total bid value
        validated_data['total_bid_value'] = (
            validated_data['bid_price_per_unit'] * validated_data['volume_requested']
        )
        
        return super().create(validated_data)


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


class BidDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed bid view"""
    ad_details = serializers.SerializerMethodField()
    bidder_details = serializers.SerializerMethodField()
    bid_ranking = serializers.SerializerMethodField()
    
    class Meta:
        model = Bid
        fields = [
            'id', 'ad_details', 'bidder_details', 'bid_price_per_unit',
            'volume_requested', 'total_bid_value', 'delivery_requirements',
            'payment_terms', 'notes', 'status', 'created_at', 'updated_at',
            'bid_ranking'
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
            'delivery_requirements', 'payment_terms', 'notes'
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
        """Update bid and recalculate total value"""
        # Recalculate total bid value if relevant fields changed
        if 'bid_price_per_unit' in validated_data or 'volume_requested' in validated_data:
            bid_price = validated_data.get('bid_price_per_unit', instance.bid_price_per_unit)
            volume = validated_data.get('volume_requested', instance.volume_requested)
            validated_data['total_bid_value'] = bid_price * volume
        
        return super().update(instance, validated_data)


class BidHistorySerializer(serializers.ModelSerializer):
    """Serializer for bid history"""
    
    class Meta:
        model = BidHistory
        fields = ['id', 'bid', 'field_changed', 'old_value', 'new_value', 'timestamp', 'notes']


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
