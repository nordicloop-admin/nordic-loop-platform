from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from base.utils.responses import APIResponse
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q, Count

# Import models
from bids.models import Bid
from company.models import Company
from users.models import User


class BaseAPIView(APIView):
    """
    Base API view that handles standard response formatting.
    """
    
    def get_response(self, api_response):
        """
        Convert an APIResponse to a DRF Response.
        
        Args:
            api_response: An APIResponse object
            
        Returns:
            A DRF Response object
        """
        return Response(
            api_response.to_dict(),
            status=api_response.code
        )
    
    def success_response(self, data=None, message="", code=status.HTTP_200_OK):
        """
        Create a success response.
        
        Args:
            data: The data to include in the response
            message: A message describing the result
            code: The HTTP status code
            
        Returns:
            A DRF Response object
        """
        api_response = APIResponse(
            success=True,
            message=message,
            data=data,
            code=code
        )
        return self.get_response(api_response)
    
    def error_response(self, message="An error occurred", code=status.HTTP_400_BAD_REQUEST, errors=None):
        """
        Create an error response.
        
        Args:
            message: A message describing the error
            code: The HTTP status code
            errors: A dictionary of field-specific errors
            
        Returns:
            A DRF Response object
        """
        api_response = APIResponse(
            success=False,
            message=message,
            code=code,
            errors=errors
        )
        return self.get_response(api_response)


class SystemStatsView(APIView):
    """
    Return counts of various entities in the system
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get counts of bids, companies, users, and pending companies
        """
        try:
            # Get query parameters for filtering
            only_active_bids = request.query_params.get('active_bids', 'false').lower() == 'true'
            
            # Build bid query
            bid_query = Q()
            if only_active_bids:
                bid_query &= Q(status__in=['active', 'winning'])
                
            # Count entities
            bids_count = Bid.objects.filter(bid_query).count()
            companies_count = Company.objects.all().count()
            users_count = User.objects.all().count()
            pending_companies_count = Company.objects.filter(status='pending').count()
            
            # Add additional bid stats
            active_bids_count = Bid.objects.filter(status='active').count()
            winning_bids_count = Bid.objects.filter(status='winning').count()
            
            return Response(
                {
                    "total_bids": bids_count,
                    "total_companies": companies_count,
                    "total_users": users_count,
                    "pending_companies": pending_companies_count,
                    "active_bids": active_bids_count,
                    "winning_bids": winning_bids_count
                },
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve system stats: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
