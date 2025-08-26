# users/serializers.py
from rest_framework import serializers
from .models import User
import re
from django.utils import timezone


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
        read_only_fields = ['id', 'company', 'company_name', 'date_joined']
        
    def validate_email(self, value):
        """
        Validate email field for uniqueness (excluding current user)
        """
        # Check if email already exists for another user
        if self.instance and self.instance.email == value:
            # Email hasn't changed, so it's valid
            return value
            
        if User.objects.filter(email=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("A user with this email already exists.")
            
        return value
        
    def update(self, instance, validated_data):
        """
        Custom update method to handle name field and email updates
        """
        # Update the name field if first_name or last_name is updated
        if 'first_name' in validated_data or 'last_name' in validated_data:
            first_name = validated_data.get('first_name', instance.first_name)
            last_name = validated_data.get('last_name', instance.last_name)
            validated_data['name'] = f"{first_name} {last_name}".strip()
            
        return super().update(instance, validated_data)


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint
    """
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value
    
    def validate_new_password(self, value):
        # Check password length
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        # Check for uppercase letter
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        # Check for number
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        return value
    
    def validate(self, data):
        # Check if new password and confirm password match
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New password and confirm password do not match."})
        
        # Check if new password is different from current password
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError({"new_password": "New password must be different from current password."})
        
        return data


class UserCompanyNameSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving only user names and their company names
    """
    company_name = serializers.CharField(source='company.official_name', read_only=True)
    registration_date = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'name', 'company_name', 'registration_date']
    
    def get_registration_date(self, obj):
        """
        Get registration date from user or company, whichever is available
        """
        if obj.date_joined:
            return obj.date_joined
        elif obj.company and obj.company.registration_date:
            return obj.company.registration_date
        return timezone.now()
