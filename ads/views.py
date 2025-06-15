from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from ads.repository import AdRepository
from ads.services import AdService
from ads.models import Ad, Subscription, Address
from ads.serializer import (
    AdCreateSerializer, AdStep1Serializer, AdStep2Serializer, AdStep3Serializer,
    AdStep4Serializer, AdStep5Serializer, AdStep6Serializer, AdStep7Serializer,
    AdStep8Serializer, AdCompleteSerializer, AdListSerializer, MarketplaceAdminSerializer,
    SubscriptionAdminSerializer, AddressAdminSerializer
)
from users.models import User
from base.utils.pagination import StandardResultsSetPagination
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

ad_repository = AdRepository()
ad_service = AdService(ad_repository)


class AdStepView(APIView):
    """Handle step-by-step ad creation and updates"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self, step):
        """Return the appropriate serializer for each step"""
        serializers = {
            1: AdStep1Serializer,
            2: AdStep2Serializer,
            3: AdStep3Serializer,
            4: AdStep4Serializer,
            5: AdStep5Serializer,
            6: AdStep6Serializer,
            7: AdStep7Serializer,
            8: AdStep8Serializer,
        }
        return serializers.get(step)

    def post(self, request, step, ad_id=None):
        """Create new ad with Step 1 data OR handle step updates via POST"""
        try:
            if ad_id is not None:
                # If ad_id is provided, this should be a PUT request
                return Response({
                    "error": "To update existing ad steps, use PUT method instead of POST",
                    "correct_method": "PUT",
                    "correct_url": f"/api/ads/{ad_id}/step/{step}/"
                }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
            if step != 1:
                return Response({"error": "New ads can only be created with Step 1 data"}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Create new ad with step 1 data
            ad = ad_service.create_ad_with_step1(request.data, request.FILES, request.user)
            
            serializer = AdStep1Serializer(ad)
            
            return Response({
                "message": "Material ad created successfully with Step 1 data. Continue with Step 2.",
                "step": 1,
                "data": serializer.data,
                "step_completion_status": ad.get_step_completion_status(),
                "next_incomplete_step": ad.get_next_incomplete_step(),
                "is_complete": ad.is_complete
            }, status=status.HTTP_201_CREATED)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to create material ad"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, ad_id=None, step=None):
        """Get current step data"""
        try:
            if not ad_id:
                return Response({"error": "Ad ID is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            if step < 1 or step > 8:
                return Response({"error": "Invalid step. Must be between 1 and 8."}, 
                              status=status.HTTP_400_BAD_REQUEST)

            ad = ad_service.get_ad_by_id(ad_id, request.user)
            if not ad:
                return Response({"error": "Ad not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer_class = self.get_serializer_class(step)
            if not serializer_class:
                return Response({"error": "Invalid step"}, status=status.HTTP_400_BAD_REQUEST)

            serializer = serializer_class(ad)
            return Response({
                "step": step,
                "data": serializer.data,
                "step_completion_status": ad.get_step_completion_status(),
                "next_incomplete_step": ad.get_next_incomplete_step()
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to retrieve step data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, ad_id, step):
        """Update specific step (for steps 1-8)"""
        try:
            if step < 1 or step > 8:
                return Response({"error": "Invalid step. Must be between 1 and 8."}, 
                              status=status.HTTP_400_BAD_REQUEST)

            ad = ad_service.update_ad_step(ad_id, step, request.data, request.FILES, request.user)
            
            serializer_class = self.get_serializer_class(step)
            serializer = serializer_class(ad)
            
            response_data = {
                "message": f"Step {step} updated successfully",
                "step": step,
                "data": serializer.data,
                "step_completion_status": ad.get_step_completion_status(),
                "next_incomplete_step": ad.get_next_incomplete_step(),
                "is_complete": ad.is_complete
            }

            if ad.is_complete:
                response_data["message"] = "Material ad completed successfully! Your material is now listed for auction."

            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to update step"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdDetailView(APIView):
    """Get complete ad details with all possible information"""
    permission_classes = [IsAuthenticated]

    def get(self, request, ad_id):
        try:
            # Optimized query to fetch all related data
            ad = Ad.objects.select_related(
                'category', 
                'subcategory', 
                'specification', 
                'location', 
                'user', 
                'user__company'
            ).filter(id=ad_id).first()
            
            if not ad:
                return Response({"error": "Ad not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = AdCompleteSerializer(ad)
            return Response({
                "message": "Ad details retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Failed to retrieve ad details"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, ad_id):
        """Update complete ad (all fields)"""
        try:
            # Get the ad with ownership check
            ad = Ad.objects.select_related('location', 'user', 'user__company').filter(
                id=ad_id, user=request.user
            ).first()
            
            if not ad:
                return Response({"error": "Ad not found or you don't have permission to edit it"}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            # Use the service to update the ad
            updated_ad = ad_service.update_complete_ad(ad_id, request.data, request.FILES, request.user)
            
            serializer = AdCompleteSerializer(updated_ad)
            return Response({
                "message": "Ad updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to update ad"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, ad_id):
        """Partially update ad (only provided fields)"""
        try:
            # Get the ad with ownership check
            ad = Ad.objects.select_related('location', 'user', 'user__company').filter(
                id=ad_id, user=request.user
            ).first()
            
            if not ad:
                return Response({"error": "Ad not found or you don't have permission to edit it"}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            # Use the service to partially update the ad
            updated_ad = ad_service.partial_update_ad(ad_id, request.data, request.FILES, request.user)
            
            serializer = AdCompleteSerializer(updated_ad)
            return Response({
                "message": "Ad partially updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to partially update ad"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, ad_id):
        """Delete an ad"""
        try:
            # Get the ad details before deletion for the response
            ad = Ad.objects.filter(id=ad_id, user=request.user).first()
            if not ad:
                return Response({"error": "Ad not found or you don't have permission to delete it"}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            # Store ad details for response
            ad_title = ad.title or f"Ad #{ad_id}"
            
            # Delete the ad
            ad_service.delete_ad(ad_id, request.user)
            
            return Response({
                "message": "Ad deleted successfully",
                "deleted_ad": {
                    "id": ad_id,
                    "title": ad_title
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to delete ad"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdListView(ListAPIView):
    """List ads with optional filtering and pagination"""
    serializer_class = AdListSerializer
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        """Get filtered queryset based on query parameters"""
        query = Q()
        
        # Get query parameters for filtering
        category_id = self.request.query_params.get('category')
        subcategory_id = self.request.query_params.get('subcategory')
        origin = self.request.query_params.get('origin')
        contamination = self.request.query_params.get('contamination')
        location_country = self.request.query_params.get('country')
        location_city = self.request.query_params.get('city')
        only_complete = self.request.query_params.get('complete', 'true').lower() == 'true'

        if only_complete:
            query &= Q(is_complete=True, is_active=True)
        
        # Apply filters
        if category_id:
            query &= Q(category_id=category_id)
        if subcategory_id:
            query &= Q(subcategory_id=subcategory_id)
        if origin:
            query &= Q(origin=origin)
        if contamination:
            query &= Q(contamination=contamination)
        if location_country:
            query &= Q(location__country__icontains=location_country)
        if location_city:
            query &= Q(location__city__icontains=location_city)

        return Ad.objects.filter(query).select_related(
            'category', 'subcategory', 'location', 'user'
        ).order_by('-created_at')


class UserAdsView(ListAPIView):
    """List current user's ads with pagination"""
    serializer_class = AdListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get user's ads based on query parameters"""
        only_complete = self.request.query_params.get('complete', 'false').lower() == 'true'
        
        query = Q(user=self.request.user)
        if only_complete:
            query &= Q(is_complete=True)

        return Ad.objects.filter(query).select_related(
            'category', 'subcategory', 'location'
        ).order_by('-updated_at')


class AdStepValidationView(APIView):
    """Validate step data without saving"""
    permission_classes = [IsAuthenticated]

    def post(self, request, step):
        try:
            if step < 1 or step > 8:
                return Response({"error": "Invalid step. Must be between 1 and 8."}, 
                              status=status.HTTP_400_BAD_REQUEST)

            # Get the appropriate serializer
            serializer_class = AdStepView().get_serializer_class(step)
            if not serializer_class:
                return Response({"error": "Invalid step"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate data without saving
            serializer = serializer_class(data=request.data)
            if serializer.is_valid():
                return Response({
                    "valid": True,
                    "message": f"Step {step} data is valid"
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "valid": False,
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": "Validation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdActivateView(APIView):
    """Activate an ad for auction/bidding"""
    permission_classes = [IsAuthenticated]

    def post(self, request, ad_id):
        """Activate/publish an ad to make it visible and available for bidding"""
        try:
            ad = ad_service.activate_ad(ad_id, request.user)
            
            return Response({
                "message": "Ad activated successfully and is now live for auction",
                "ad": {
                    "id": ad.id,
                    "title": ad.title,
                    "is_active": ad.is_active,
                    "is_complete": ad.is_complete,
                    "auction_start_date": ad.auction_start_date,
                    "auction_end_date": ad.auction_end_date,
                    "auction_duration_display": ad.get_auction_duration_display()
                }
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to activate ad"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdDeactivateView(APIView):
    """Deactivate an ad to stop auction/bidding"""
    permission_classes = [IsAuthenticated]

    def post(self, request, ad_id):
        """Deactivate/unpublish an ad to make it invisible and stop bidding"""
        try:
            ad = ad_service.deactivate_ad(ad_id, request.user)
            
            return Response({
                "message": "Ad deactivated successfully and is no longer visible for bidding",
                "ad": {
                    "id": ad.id,
                    "title": ad.title,
                    "is_active": ad.is_active,
                    "is_complete": ad.is_complete
                }
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to deactivate ad"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketplaceAdminViewSet(viewsets.ModelViewSet):
    queryset = Ad.objects.select_related('category', 'user', 'user__company', 'location').all().order_by('-created_at')
    serializer_class = MarketplaceAdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'category__name', 'user__company__official_name', 'location__country']
    filterset_fields = ['status']

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        ad = self.get_object()
        status_value = request.data.get('status')
        if status_value not in ['active', 'pending', 'inactive']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        ad.status = status_value
        ad.save()
        serializer = self.get_serializer(ad)
        return Response(serializer.data)


class SubscriptionAdminViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.select_related('company').all().order_by('-start_date')
    serializer_class = SubscriptionAdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['company__official_name', 'contact_name', 'contact_email']
    filterset_fields = ['plan', 'status']

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        subscription = self.get_object()
        status_value = request.data.get('status')
        if status_value not in dict(Subscription.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        subscription.status = status_value
        subscription.save()
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)


class AddressAdminViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.select_related('company').all().order_by('-created_at')
    serializer_class = AddressAdminSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['company__official_name', 'contact_name', 'contact_phone', 'city', 'country']
    filterset_fields = ['type', 'is_verified']

    @action(detail=True, methods=['patch'], url_path='verify')
    def verify_address(self, request, pk=None):
        address = self.get_object()
        is_verified = request.data.get('isVerified')
        if is_verified is None:
            return Response({'error': 'Missing isVerified field'}, status=status.HTTP_400_BAD_REQUEST)
        address.is_verified = bool(is_verified)
        address.save()
        serializer = self.get_serializer(address)
        return Response(serializer.data)
