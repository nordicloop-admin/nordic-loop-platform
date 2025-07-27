from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the Notification model
    """
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'date', 'is_read', 'type', 'priority', 'action_url', 'metadata', 'user', 'subscription_target']
        read_only_fields = ['id', 'date']

class CreateNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for creating notifications
    """
    class Meta:
        model = Notification
        fields = ['title', 'message', 'type', 'priority', 'action_url', 'metadata', 'user', 'subscription_target']
