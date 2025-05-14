# users/serializers.py
from rest_framework import serializers
from .models import User
from company.serializer import CompanySerializer

class UserSerializer(serializers.ModelSerializer):
    company = CompanySerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'date_joined', 'company']
