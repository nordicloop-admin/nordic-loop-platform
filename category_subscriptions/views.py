from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import CategorySubscription
from .serializers import CategorySubscriptionSerializer
from category.models import Category, SubCategory

class CategorySubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing category subscriptions
    """
    serializer_class = CategorySubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Return subscriptions for the current user
        """
        return CategorySubscription.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Set the user to the current user when creating a subscription
        """
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def subscribe_category(self, request):
        """
        Subscribe to a category
        """
        category_id = request.data.get('category_id')
        if not category_id:
            return Response({'error': 'Category ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        category = get_object_or_404(Category, id=category_id)
        
        # Check if subscription already exists
        existing = CategorySubscription.objects.filter(
            user=request.user,
            category=category,
            subcategory__isnull=True
        ).first()
        
        if existing:
            return Response({'error': 'Already subscribed to this category'}, status=status.HTTP_400_BAD_REQUEST)
        
        subscription = CategorySubscription.objects.create(
            user=request.user,
            category=category
        )
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def subscribe_subcategory(self, request):
        """
        Subscribe to a subcategory
        """
        subcategory_id = request.data.get('subcategory_id')
        if not subcategory_id:
            return Response({'error': 'Subcategory ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        subcategory = get_object_or_404(SubCategory, id=subcategory_id)
        
        # Check if subscription already exists
        existing = CategorySubscription.objects.filter(
            user=request.user,
            category=subcategory.category,
            subcategory=subcategory
        ).first()
        
        if existing:
            return Response({'error': 'Already subscribed to this subcategory'}, status=status.HTTP_400_BAD_REQUEST)
        
        subscription = CategorySubscription.objects.create(
            user=request.user,
            category=subcategory.category,
            subcategory=subcategory
        )
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """
        Unsubscribe from a category or subcategory
        """
        subscription_id = request.data.get('subscription_id')
        if not subscription_id:
            return Response({'error': 'Subscription ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        subscription = get_object_or_404(CategorySubscription, id=subscription_id, user=request.user)
        subscription.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def check_subscription(self, request):
        """
        Check if user is subscribed to a category or subcategory
        """
        category_id = request.query_params.get('category_id')
        subcategory_id = request.query_params.get('subcategory_id')
        
        if not category_id:
            return Response({'error': 'Category ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        query = Q(user=request.user, category_id=category_id)
        
        if subcategory_id:
            query &= Q(subcategory_id=subcategory_id)
        else:
            query &= Q(subcategory__isnull=True)
        
        is_subscribed = CategorySubscription.objects.filter(query).exists()
        
        return Response({'is_subscribed': is_subscribed})
