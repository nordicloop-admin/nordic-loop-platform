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
            'ad', 'bid_price_per_unit', 'volume_requested', 'volume_type',
            'notes', 'max_auto_bid_price'
        ]
        
    def validate(self, data):
        """Validate bid data against ad requirements"""
        ad = data.get('ad')
        bid_price = data.get('bid_price_per_unit')
        volume = data.get('volume_requested')
        
        if not ad:
            raise serializers.ValidationError("Ad is required")
            
        # Check if ad is active
        if not ad.is_active:
            raise serializers.ValidationError("Cannot bid on inactive ads")
        
        # Check if auction has ended
        if ad.auction_end_date and ad.auction_end_date < timezone.now():
            raise serializers.ValidationError("Auction has ended")
        
        # Check minimum bid requirements
        if ad.starting_bid_price and bid_price < ad.starting_bid_price:
            raise serializers.ValidationError(
                f"Bid price must be at least {ad.starting_bid_price} {ad.currency}"
            )
        
        # Check if this bid is higher than current highest
        highest_bid = Bid.objects.filter(
            ad=ad, 
            status__in=['active', 'winning']
        ).order_by('-bid_price_per_unit').first()
        
        if highest_bid and bid_price <= highest_bid.bid_price_per_unit:
            raise serializers.ValidationError(
                f"Bid must be higher than current highest bid of {highest_bid.bid_price_per_unit} {ad.currency}"
            )
        
        # Check volume requirements
        if ad.minimum_order_quantity and volume < ad.minimum_order_quantity:
            raise serializers.ValidationError(
                f"Volume must be at least {ad.minimum_order_quantity} {ad.unit_of_measurement}"
            )
        
        if volume > ad.available_quantity:
            raise serializers.ValidationError(
                f"Volume cannot exceed available quantity of {ad.available_quantity} {ad.unit_of_measurement}"
            )
        
        return data

    def create(self, validated_data):
        """Create bid and update statuses of existing bids"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['user'] = request.user
        
        # Check if user already has a bid for this ad
        existing_bid = Bid.objects.filter(
            user=validated_data['user'],
            ad=validated_data['ad']
        ).first()
        
        if existing_bid:
            # Update existing bid instead of creating new one
            for attr, value in validated_data.items():
                setattr(existing_bid, attr, value)
            existing_bid.save()
            return existing_bid
        
        # Create new bid
        bid = Bid.objects.create(**validated_data)
        
        # Update status of other bids for this ad
        Bid.objects.filter(
            ad=bid.ad,
            status='winning'
        ).exclude(id=bid.id).update(status='outbid')
        
        # Set this bid as winning if it's the highest
        if bid.is_winning:
            bid.status = 'winning'
            bid.save()
        
        return bid


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
    """Serializer for listing bids with basic info"""
    bidder_name = serializers.CharField(source='user.username', read_only=True)
    ad_title = serializers.CharField(source='ad.title', read_only=True)
    currency = serializers.CharField(source='ad.currency', read_only=True)
    unit = serializers.CharField(source='ad.unit_of_measurement', read_only=True)
    is_winning = serializers.BooleanField(read_only=True)
    rank = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id', 'bidder_name', 'ad_title', 'bid_price_per_unit', 'volume_requested',
            'total_bid_value', 'currency', 'unit', 'status', 'is_winning', 'rank',
            'created_at', 'updated_at'
        ]


class BidDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single bid view"""
    bidder = UserSerializer(source='user', read_only=True)
    ad_details = AdBasicSerializer(source='ad', read_only=True)
    is_winning = serializers.BooleanField(read_only=True)
    rank = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Bid
        fields = [
            'id', 'bidder', 'ad_details', 'bid_price_per_unit', 'volume_requested',
            'volume_type', 'total_bid_value', 'status', 'is_auto_bid',
            'max_auto_bid_price', 'notes', 'is_winning', 'rank',
            'created_at', 'updated_at'
        ]


class BidUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing bids"""
    
    class Meta:
        model = Bid
        fields = ['bid_price_per_unit', 'volume_requested', 'notes', 'max_auto_bid_price']
    
    def validate_bid_price_per_unit(self, value):
        """Ensure new bid price is higher than current highest"""
        bid = self.instance
        if bid:
            ad = bid.ad
            
            # Check if new price meets minimum requirements
            if ad.starting_bid_price and value < ad.starting_bid_price:
                raise serializers.ValidationError(
                    f"Bid price must be at least {ad.starting_bid_price} {ad.currency}"
                )
            
            # Check if new price is higher than other bids
            highest_bid = Bid.objects.filter(
                ad=ad,
                status__in=['active', 'winning']
            ).exclude(id=bid.id).order_by('-bid_price_per_unit').first()
            
            if highest_bid and value <= highest_bid.bid_price_per_unit:
                raise serializers.ValidationError(
                    f"Bid must be higher than current highest bid of {highest_bid.bid_price_per_unit} {ad.currency}"
                )
        
        return value

    def update(self, instance, validated_data):
        """Update bid and create history entry"""
        # Store previous values for history
        previous_price = instance.bid_price_per_unit
        previous_volume = instance.volume_requested
        
        # Update bid
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Create history entry
        BidHistory.objects.create(
            bid=instance,
            previous_price=previous_price,
            new_price=instance.bid_price_per_unit,
            previous_volume=previous_volume,
            new_volume=instance.volume_requested,
            change_reason='bid_updated'
        )
        
        # Update other bid statuses
        if instance.is_winning:
            Bid.objects.filter(
                ad=instance.ad,
                status='winning'
            ).exclude(id=instance.id).update(status='outbid')
            instance.status = 'winning'
            instance.save()
        
        return instance


class BidHistorySerializer(serializers.ModelSerializer):
    """Serializer for bid history"""
    
    class Meta:
        model = BidHistory
        fields = [
            'id', 'previous_price', 'new_price', 'previous_volume', 'new_volume',
            'change_reason', 'timestamp'
        ]


class BidStatsSerializer(serializers.Serializer):
    """Serializer for bid statistics on an ad"""
    total_bids = serializers.IntegerField()
    highest_bid = serializers.DecimalField(max_digits=12, decimal_places=2)
    lowest_bid = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_bid = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_volume_requested = serializers.DecimalField(max_digits=15, decimal_places=2)
    unique_bidders = serializers.IntegerField()


class BidAdminSerializer(serializers.ModelSerializer):
    itemId = serializers.CharField(source='ad.id', read_only=True)
    itemName = serializers.CharField(source='ad.title', read_only=True)
    bidAmount = serializers.DecimalField(source='bid_price_per_unit', max_digits=12, decimal_places=2)
    previousBid = serializers.SerializerMethodField()
    bidderName = serializers.CharField(source='user.get_full_name', read_only=True)
    bidderCompany = serializers.CharField(source='user.company.official_name', read_only=True)
    bidderEmail = serializers.EmailField(source='user.email', read_only=True)
    isHighest = serializers.SerializerMethodField()
    createdAt = serializers.DateTimeField(source='created_at')
    expiresAt = serializers.SerializerMethodField()
    needsReview = serializers.SerializerMethodField()
    id = serializers.CharField(source='pk')

    class Meta:
        model = Bid
        fields = [
            'id', 'itemId', 'itemName', 'bidAmount', 'previousBid', 'bidderName', 'bidderCompany',
            'bidderEmail', 'status', 'isHighest', 'createdAt', 'expiresAt', 'needsReview'
        ]

    def get_previousBid(self, obj):
        # Get the previous highest bid for the same ad before this bid
        previous = Bid.objects.filter(ad=obj.ad, created_at__lt=obj.created_at).order_by('-created_at').first()
        return previous.bid_price_per_unit if previous else None

    def get_isHighest(self, obj):
        return obj.is_winning

    def get_expiresAt(self, obj):
        # Use ad's auction_end_date if available
        return obj.ad.auction_end_date if obj.ad and obj.ad.auction_end_date else None

    def get_needsReview(self, obj):
        # Placeholder: implement logic if needed
        return False
