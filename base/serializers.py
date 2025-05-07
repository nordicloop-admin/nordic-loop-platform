from rest_framework import serializers
from base.models import Address


class AddressSerializer(serializers.ModelSerializer):
    """
    Serializer for the Address model.
    """
    
    class Meta:
        model = Address
        fields = [
            'id', 'country', 'province', 'district', 'city', 
            'street_number', 'code', 'additional_info'
        ]
        read_only_fields = ['id']
