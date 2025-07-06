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


class UserDashboardStatsView(APIView):
    """
    Return personalized dashboard statistics for the logged-in user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get user-specific dashboard statistics including:
        - Active bids count
        - Subscription information
        - Verification status
        - Recent activities
        """
        try:
            user = request.user
            company = user.company if hasattr(user, 'company') else None
            
            # Count user's active bids
            active_bids_count = Bid.objects.filter(
                user=user,
                status='active'
            ).count()
            
            # Count user's winning bids
            winning_bids_count = Bid.objects.filter(
                user=user,
                status='winning'
            ).count()
            
            # Count user's total bids
            total_user_bids = Bid.objects.filter(user=user).count()
            
            # Get user's recent bids
            recent_bids = Bid.objects.filter(user=user).order_by('-created_at')[:5]
            recent_bids_data = []
            for bid in recent_bids:
                bid_data = {
                    'id': bid.id,
                    'status': bid.status,
                    'price': float(bid.bid_price_per_unit),
                    'created_at': bid.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                }
                # Try to get ad info safely
                try:
                    if hasattr(bid, 'ad') and bid.ad:
                        bid_data['ad_id'] = bid.ad.id
                except:
                    bid_data['ad_id'] = None
                
                recent_bids_data.append(bid_data)
            
            # Get user's active ads (if applicable)
            ads_count = 0
            recent_ads_data = []
            from ads.models import Ad
            if hasattr(user, 'can_place_ads') and user.can_place_ads:
                # Count active ads
                ads_count = Ad.objects.filter(
                    user=user,
                    is_active=True
                ).count()
                
                # Get recent ads
                recent_ads = Ad.objects.filter(user=user).order_by('-created_at')[:5]
                for ad in recent_ads:
                    ad_data = {
                        'id': ad.id,
                        'title': ad.title if hasattr(ad, 'title') else 'Ad',
                        'status': 'active' if ad.is_active else 'inactive',
                        'created_at': ad.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                    # Try to get bids count safely
                    try:
                        ad_data['bids_count'] = Bid.objects.filter(ad=ad).count()
                    except:
                        ad_data['bids_count'] = 0
                        
                    recent_ads_data.append(ad_data)
            
            # Build the response
            response_data = {
                "user_id": user.id,
                "username": user.username,
                "active_bids": active_bids_count,
                "winning_bids": winning_bids_count,
                "total_bids": total_user_bids,
                "active_ads": ads_count,
                "recent_bids": recent_bids_data,
                "recent_ads": recent_ads_data
            }
            
            # Add company information if available
            if company:
                response_data.update({
                    "company_id": company.id,
                    "company_name": company.official_name,
                    "subscription": "Free Plan",  # This should be replaced with actual subscription logic
                    "verification_status": company.status,
                    "is_verified": company.status == "approved",
                    "pending_verification": company.status == "pending"
                })
                
                # Add verification message if pending
                if company.status == "pending":
                    response_data["verification_message"] = "Your business is under verification"
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve user dashboard stats: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
