# users/serializers.py
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.official_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'name', 'company', 'company_name', 'role', 'date_joined']


class AdminUserListSerializer(serializers.ModelSerializer):
    """
    Admin serializer for user list view with specific field mapping
    """
    firstName = serializers.CharField(source='first_name', read_only=True)
    lastName = serializers.CharField(source='last_name', read_only=True)
    companyName = serializers.CharField(source='company.official_name', read_only=True)
    status = serializers.SerializerMethodField()
    lastLogin = serializers.DateTimeField(source='last_login', read_only=True)
    joinDate = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'firstName',
            'lastName',
            'email',
            'companyName',
            'role',
            'status',
            'lastLogin',
            'joinDate'
        ]

    def get_status(self, obj):
        """
        Convert is_active boolean to status string
        """
        return "active" if obj.is_active else "inactive"

    def get_joinDate(self, obj):
        """
        Convert datetime to date string
        """
        if obj.date_joined:
            return obj.date_joined.date()
        return None


class AdminUserDetailSerializer(AdminUserListSerializer):
    """
    Admin serializer for user detail view - extends list serializer
    """
    # Add any additional fields for detail view if needed
    username = serializers.CharField(read_only=True)
    canPlaceAds = serializers.BooleanField(source='can_place_ads', read_only=True)
    canPlaceBids = serializers.BooleanField(source='can_place_bids', read_only=True)
    
    class Meta(AdminUserListSerializer.Meta):
        fields = AdminUserListSerializer.Meta.fields + ['username', 'canPlaceAds', 'canPlaceBids']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile retrieval and update
    """
    company_name = serializers.CharField(source='company.official_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'name',
            'company', 'company_name', 'role', 'role_display',
            'can_place_ads', 'can_place_bids', 'date_joined'
        ]
        read_only_fields = ['id', 'email', 'company', 'company_name', 'date_joined']
        
    def update(self, instance, validated_data):
        """
        Custom update method to handle name field
        """
        # Update the name field if first_name or last_name is updated
        if 'first_name' in validated_data or 'last_name' in validated_data:
            first_name = validated_data.get('first_name', instance.first_name)
            last_name = validated_data.get('last_name', instance.last_name)
            validated_data['name'] = f"{first_name} {last_name}".strip()
            
        return super().update(instance, validated_data)
