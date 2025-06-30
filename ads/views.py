from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import Http404
from ads.repository import AdRepository
from ads.services import AdService
from ads.models import Ad
from ads.serializer import (
    AdCreateSerializer, AdStep1Serializer, AdStep2Serializer, AdStep3Serializer,
    AdStep4Serializer, AdStep5Serializer, AdStep6Serializer, AdStep7Serializer,
    AdStep8Serializer, AdCompleteSerializer, AdListSerializer, AdUpdateSerializer,
    AdminAuctionListSerializer, AdminAuctionDetailSerializer,
    AdminAddressListSerializer, AdminAddressDetailSerializer
)
from users.models import User
from base.utils.pagination import StandardResultsSetPagination

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


class AdminAuctionListView(APIView):
    """
    Admin endpoint for listing auctions with filtering and pagination
    GET /api/ads/admin/auctions/
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # Get query parameters
            search = request.query_params.get('search', None)
            status_filter = request.query_params.get('status', None)
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))

            # Validate status parameter
            if status_filter and status_filter != 'all':
                valid_statuses = ['active', 'inactive', 'pending', 'draft']
                if status_filter not in valid_statuses:
                    return Response(
                        {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Get filtered ads
            pagination_data = ad_service.get_admin_ads_filtered(
                search=search,
                status=status_filter,
                page=page,
                page_size=page_size
            )

            # Serialize the results
            serializer = AdminAuctionListSerializer(pagination_data['results'], many=True)
            
            # Format response according to specification
            response_data = {
                "count": pagination_data['count'],
                "next": pagination_data['next'],
                "previous": pagination_data['previous'],
                "results": serializer.data,
                "page_size": pagination_data['page_size'],
                "total_pages": pagination_data['total_pages'],
                "current_page": pagination_data['current_page']
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": f"ValueError: {str(ve)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return Response(
                {
                    "error": "Failed to retrieve auctions",
                    "details": str(e),
                    "traceback": error_details
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminAuctionDetailView(APIView):
    """
    Admin endpoint for retrieving a specific auction
    GET /api/ads/admin/auctions/{id}/
    """
    permission_classes = [IsAdminUser]

    def get(self, request, ad_id):
        try:
            ad = ad_service.get_ad_by_id(ad_id)
            if not ad:
                return Response(
                    {"error": "Auction not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = AdminAuctionDetailSerializer(ad)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Failed to retrieve auction"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminAddressListView(APIView):
    """
    Admin endpoint for listing addresses with filtering and pagination
    GET /api/ads/admin/addresses/
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            # Get query parameters
            search = request.query_params.get('search', None)
            type_filter = request.query_params.get('type', None)
            is_verified_param = request.query_params.get('is_verified', None)
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 10)), 100)

            # Parse is_verified parameter
            is_verified = None
            if is_verified_param is not None:
                is_verified = is_verified_param.lower() in ('true', '1', 'yes')

            # Get filtered addresses
            pagination_data = ad_service.get_admin_addresses_filtered(
                search=search,
                type_filter=type_filter,
                is_verified=is_verified,
                page=page,
                page_size=page_size
            )

            # Serialize the data
            serializer = AdminAddressListSerializer(pagination_data['results'], many=True)

            return Response({
                'count': pagination_data['count'],
                'next': pagination_data['next'],
                'previous': pagination_data['previous'],
                'results': serializer.data,
                'page_size': pagination_data['page_size'],
                'total_pages': pagination_data['total_pages'],
                'current_page': pagination_data['current_page']
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to retrieve addresses',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminAddressDetailView(APIView):
    """
    Admin endpoint for retrieving a specific address
    GET /api/ads/admin/addresses/{id}/
    """
    permission_classes = [IsAdminUser]

    def get(self, request, address_id):
        try:
            # Get address by ID
            address = ad_service.get_address_by_id(address_id)
            
            if not address:
                return Response({
                    'error': 'Address not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Serialize the data
            serializer = AdminAddressDetailSerializer(address)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to retrieve address',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminAddressVerifyView(APIView):
    """
    Admin endpoint for verifying/unverifying addresses
    PATCH /api/ads/admin/addresses/{id}/verify/
    """
    permission_classes = [IsAdminUser]

    def patch(self, request, address_id):
        try:
            # Get is_verified status from request
            is_verified = request.data.get('isVerified')
            
            if is_verified is None:
                return Response({
                    'error': 'isVerified field is required',
                    'example': {'isVerified': True}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update address verification status
            address = ad_service.update_address_verification(address_id, is_verified)
            
            if not address:
                return Response({
                    'error': 'Address not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Serialize the updated address
            serializer = AdminAddressDetailSerializer(address)

            verification_action = "verified" if is_verified else "unverified"
            return Response({
                'message': f'Address successfully {verification_action}',
                'address': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to update address verification',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
