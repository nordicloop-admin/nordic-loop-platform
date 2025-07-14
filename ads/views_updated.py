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
from .serializer import (
    AdCreateSerializer, AdStep1Serializer, AdStep2Serializer, AdStep3Serializer,
    AdStep4Serializer, AdStep5Serializer, AdStep6Serializer, AdStep7Serializer,
    AdStep8Serializer, AdCompleteSerializer, AdListSerializer, AdUpdateSerializer,
    AdminAuctionListSerializer, AdminAuctionDetailSerializer,
    AdminAddressListSerializer, AdminAddressDetailSerializer,
    AdminSubscriptionListSerializer, AdminSubscriptionDetailSerializer,
    UserSubscriptionSerializer, UpdateUserSubscriptionSerializer,
    UserAddressSerializer, CreateAddressSerializer, UpdateAddressSerializer
)
from users.models import User
from base.utils.pagination import StandardResultsSetPagination

ad_repository = AdRepository()
ad_service = AdService(ad_repository)


class AdStepView(APIView):
    """Handle step-by-step ad creation and updates"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self, step, ad=None):
        """Return the appropriate serializer for each step"""
        # Check if this is a plastic material (category_id 1 is assumed to be plastic)
        is_plastic = ad and ad.category and ad.category.id == 1
        
        if is_plastic:
            # Full pathway for plastics
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
        else:
            # Shortened pathway for other materials - keeping original step numbers
            serializers = {
                1: AdStep1Serializer,
                6: AdStep6Serializer,  # Location & Logistics
                7: AdStep7Serializer,  # Quantity & Price
                8: AdStep8Serializer,  # Image & Description
            }
        return serializers.get(step)
    
    def validate_step(self, step, ad):
        """Validate step number based on material category"""
        # Check if this is a plastic material (category_id 1 is assumed to be plastic)
        is_plastic = ad and ad.category and ad.category.id == 1
        
        if is_plastic:
            # For plastics, steps are 1-8
            if step < 1 or step > 8:
                return Response({
                    "error": "Invalid step. For plastics, must be between 1 and 8."
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # For other materials, steps are 1, 6, 7, 8
            valid_steps = [1, 6, 7, 8]
            if step not in valid_steps:
                return Response({
                    "error": "Invalid step. For this material type, valid steps are 1, 6, 7, and 8."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return None  # No error

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
            
            ad = ad_service.get_ad_by_id(ad_id, request.user)
            if not ad:
                return Response({"error": "Ad not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Validate step based on material category
            error_response = self.validate_step(step, ad)
            if error_response:
                return error_response

            serializer_class = self.get_serializer_class(step, ad)
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
            ad = ad_service.get_ad_by_id(ad_id, request.user)
            if not ad:
                return Response({"error": "Ad not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Validate step based on material category
            error_response = self.validate_step(step, ad)
            if error_response:
                return error_response

            serializer_class = self.get_serializer_class(step, ad)
            if not serializer_class:
                return Response({"error": "Invalid step"}, status=status.HTTP_400_BAD_REQUEST)

            ad = ad_service.update_ad_step(ad_id, step, request.data, request.FILES, request.user)
            
            serializer = serializer_class(ad)
            
            response_data = {
                "message": f"Step {step} updated successfully.",
                "step": step,
                "data": serializer.data,
                "step_completion_status": ad.get_step_completion_status(),
                "next_incomplete_step": ad.get_next_incomplete_step(),
                "is_complete": ad.is_complete
            }
            
            # If this is the last step and it's complete, add a note about activation
            if step == 8 and ad.get_step_completion_status().get(8, False):
                response_data["note"] = "All steps are complete. You can now activate the ad for bidding."
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to update step data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
