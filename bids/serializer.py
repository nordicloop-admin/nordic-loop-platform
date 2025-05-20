from .models import Bid
from rest_framework import serializers
from users.serializers import UserSerializer

class BidSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(read_only=True, slug_field='name')

    class Meta:
        model = Bid
        fields = ['id', 'user', 'ad', 'amount', 'timestamp']
        read_only_fields = ['id', 'timestamp']
