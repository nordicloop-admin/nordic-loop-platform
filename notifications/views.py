from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Notification
from .serializers import NotificationSerializer, CreateNotificationSerializer
from .permissions import IsAdminUser
import json

class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for handling user notifications
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'delete']
    
    def get_queryset(self):
        # Regular users can only see their own notifications
        user = self.request.user
        if not user.is_staff and not user.is_superuser and user.role != 'Admin':
            return Notification.objects.filter(Q(user=user) | Q(user=None))
        # Admin users can see all notifications if using admin endpoints
        if self.action in ['list_all', 'create_notification', 'broadcast', 'delete_broadcast']:
            return Notification.objects.all()
        # Otherwise return their own notifications
        return Notification.objects.filter(Q(user=user) | Q(user=None))
    
    def list(self, request):
        """
        Get all notifications for the current user
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        """
        Get all unread notifications for the current user
        """
        queryset = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Get count of unread notifications for the current user
        """
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Get notification statistics for the current user
        """
        queryset = self.get_queryset()
        total_count = queryset.count()
        unread_count = queryset.filter(is_read=False).count()

        # Count by type
        type_counts = {}
        for notification_type, _ in Notification.NOTIFICATION_TYPES:
            type_counts[notification_type] = queryset.filter(type=notification_type).count()

        # Count by priority
        priority_counts = {}
        for priority, _ in Notification.PRIORITY_CHOICES:
            priority_counts[priority] = queryset.filter(priority=priority).count()

        return Response({
            'total_count': total_count,
            'unread_count': unread_count,
            'read_count': total_count - unread_count,
            'type_counts': type_counts,
            'priority_counts': priority_counts
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='mark-type-as-read')
    def mark_type_as_read(self, request):
        """
        Mark all notifications of a specific type as read
        """
        notification_type = request.data.get('type')
        if not notification_type:
            return Response({'error': 'Type is required'}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = self.get_queryset().filter(
            type=notification_type,
            is_read=False
        ).update(is_read=True)

        return Response({
            'success': True,
            'updated_count': updated_count,
            'type': notification_type
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['put'], url_path='read')
    def read(self, request, pk=None):
        """
        Mark a notification as read
        """
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], url_path='read-all')
    def read_all(self, request):
        """
        Mark all notifications as read for the current user
        """
        queryset = self.get_queryset().filter(is_read=False)
        updated_count = queryset.update(is_read=True)
        return Response({'success': True, 'count': updated_count})
    
    # Admin endpoints
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser], url_path='list-all')
    def list_all(self, request):
        """
        Get all notifications (admin only)
        """
        queryset = Notification.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser], url_path='create-notification')
    def create_notification(self, request):
        """
        Create a new notification (admin only)
        """
        data = request.data.copy()
        
        # Handle userId parameter if present
        if 'userId' in data and not 'user' in data:
            data['user'] = data.pop('userId')
            
        serializer = CreateNotificationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser], url_path='broadcast')
    def broadcast(self, request):
        """
        Create a notification for all users (admin only)
        """
        serializer = CreateNotificationSerializer(data=request.data)
        if serializer.is_valid():
            # Create a system notification with no specific user (broadcast)
            notification = serializer.save(user=None)
            return Response({
                'success': True,
                'notification_id': notification.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'], permission_classes=[IsAdminUser], url_path='delete-broadcast')
    def delete_broadcast(self, request, pk=None):
        """
        Delete a notification for all users (admin only)
        """
        notification = self.get_object()
        notification.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
