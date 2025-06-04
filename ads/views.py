from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ads.repository import AdRepository
from ads.services import AdService
from ads.serializer import (
    AdCreateSerializer, AdStep1Serializer, AdStep2Serializer, AdStep3Serializer,
    AdStep4Serializer, AdStep5Serializer, AdStep6Serializer, AdStep7Serializer,
    AdStep8Serializer, AdCompleteSerializer, AdListSerializer
)
from users.models import User

ad_repository = AdRepository()
ad_service = AdService(ad_repository)


class AdCreateView(APIView):
    """Create a new ad (returns ad ID for step-by-step completion)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            ad = ad_service.create_new_ad(request.user)
            serializer = AdCreateSerializer(ad)
            return Response({
                "message": "Ad created successfully. Continue with step 1.",
                "ad": serializer.data
            }, status=status.HTTP_201_CREATED)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to create ad"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdStepView(APIView):
    """Handle individual step updates"""
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

    def get(self, request, ad_id, step):
        """Get current step data"""
        try:
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
        """Update specific step"""
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
                response_data["message"] = "Ad completed successfully! Your material is now listed for auction."

            return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to update step"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdDetailView(APIView):
    """Get complete ad details"""
    permission_classes = [IsAuthenticated]

    def get(self, request, ad_id):
        try:
            ad = ad_service.get_ad_by_id(ad_id)
            if not ad:
                return Response({"error": "Ad not found"}, status=status.HTTP_404_NOT_FOUND)

            serializer = AdCompleteSerializer(ad)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Failed to retrieve ad"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, ad_id):
        """Delete an ad"""
        try:
            ad_service.delete_ad(ad_id, request.user)
            return Response({"message": "Ad deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Failed to delete ad"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdListView(APIView):
    """List ads with optional filtering"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get query parameters for filtering
            category_id = request.query_params.get('category')
            subcategory_id = request.query_params.get('subcategory')
            origin = request.query_params.get('origin')
            contamination = request.query_params.get('contamination')
            location_country = request.query_params.get('country')
            location_city = request.query_params.get('city')
            only_complete = request.query_params.get('complete', 'true').lower() == 'true'

            ads = ad_service.list_ads(
                category_id=category_id,
                subcategory_id=subcategory_id,
                origin=origin,
                contamination=contamination,
                location_country=location_country,
                location_city=location_city,
                only_complete=only_complete
            )

            serializer = AdListSerializer(ads, many=True)
            return Response({
                "count": len(ads),
                "results": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Failed to retrieve ads"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserAdsView(APIView):
    """List current user's ads"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            only_complete = request.query_params.get('complete', 'false').lower() == 'true'
            ads = ad_service.list_user_ads(request.user, only_complete)
            
            serializer = AdListSerializer(ads, many=True)
            return Response({
                "count": len(ads),
                "results": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": "Failed to retrieve user ads"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
