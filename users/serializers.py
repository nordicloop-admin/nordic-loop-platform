# users/serializers.py
from rest_framework import serializers
from .models import User
from company.serializer import CompanySerializer
from company.models import Company

class UserSerializer(serializers.ModelSerializer):
    company = CompanySerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'date_joined', 'company']

class UserAdminSerializer(serializers.ModelSerializer):
    companyId = serializers.SerializerMethodField()
    companyName = serializers.SerializerMethodField()
    firstName = serializers.CharField(source='first_name')
    lastName = serializers.CharField(source='last_name')
    position = serializers.CharField(source='role', required=False)
    createdAt = serializers.DateTimeField(source='date_joined')
    id = serializers.CharField(source='pk')

    class Meta:
        model = User
        fields = [
            'id', 'email', 'firstName', 'lastName', 'position', 'companyId', 'companyName', 'createdAt'
        ]

    def get_companyId(self, obj):
        return str(obj.company.pk) if obj.company else None

    def get_companyName(self, obj):
        return obj.company.official_name if obj.company else None
