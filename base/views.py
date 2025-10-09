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
                    status='active'
                ).count()
                
                # Get recent ads
                recent_ads = Ad.objects.filter(user=user).order_by('-created_at')[:5]
                for ad in recent_ads:
                    ad_data = {
                        'id': ad.id,
                        'title': ad.title if hasattr(ad, 'title') else 'Ad',
                        'status': ad.status,
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
                "first_name": getattr(user, 'first_name', '') or '',
                "active_bids": active_bids_count,
                "winning_bids": winning_bids_count,
                "total_bids": total_user_bids,
                "active_ads": ads_count,
                "recent_bids": recent_bids_data,
                "recent_ads": recent_ads_data
            }
            
            # Add company information if available
            if company:
                # Get actual subscription information
                subscription_display = "Free Plan"  # Default fallback
                try:
                    from ads.models import Subscription
                    subscription = Subscription.objects.filter(company=company).first()
                    if subscription:
                        # Format the plan name properly
                        plan_name = subscription.plan.replace('_', ' ').title()
                        subscription_display = f"{plan_name} Plan"
                except Exception:
                    # If there's any error getting subscription, use the default
                    subscription_display = "Free Plan"
                
                response_data.update({
                    "company_id": company.id,
                    "company_name": company.official_name,
                    "subscription": subscription_display,
                    "verification_status": company.status,
                    "is_verified": company.status == "approved",
                    "pending_verification": company.status == "pending"
                })

                # ---------------- Payment State Derivation ----------------
                # Raw payment/account fields (Stripe Connect onboarding lifecycle)
                stripe_account_id = getattr(company, 'stripe_account_id', None)
                onboarding_complete = bool(getattr(company, 'stripe_onboarding_complete', False))
                capabilities_complete = bool(getattr(company, 'stripe_capabilities_complete', False))
                payment_ready = bool(getattr(company, 'payment_ready', False))
                last_payment_check = getattr(company, 'last_payment_check', None)

                # Derive high-level state machine
                # Enum values: not_started | in_progress | capabilities_pending | finalizing | ready
                if not stripe_account_id:
                    payment_state = 'not_started'
                elif not onboarding_complete:
                    payment_state = 'in_progress'
                elif onboarding_complete and not capabilities_complete:
                    payment_state = 'capabilities_pending'
                elif capabilities_complete and not payment_ready:
                    payment_state = 'finalizing'
                else:
                    payment_state = 'ready'

                payment_block = {
                    "account_id": stripe_account_id,
                    "onboarding_complete": onboarding_complete,
                    "capabilities_complete": capabilities_complete,
                    "payment_ready": payment_ready,
                    "last_payment_check": last_payment_check.isoformat() if last_payment_check else None
                }

                response_data["payment"] = payment_block
                response_data["payment_state"] = payment_state
                
                # Add verification message based on status
                if company.status == "pending":
                    response_data["verification_message"] = "Your business is under verification. Verification typically takes 1–2 business days."
                elif company.status == "rejected":
                    response_data["verification_message"] = "Business verification was rejected. Please contact support."
                elif company.status == "approved":
                    response_data["verification_message"] = "Your business is verified"
                else:
                    response_data["verification_message"] = f"Business status: {company.status}"
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve user dashboard stats: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TotalBidsCountView(APIView):
    """
    Return the total number of bids in the system with optional filtering
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Get the total count of bids in the system with optional filtering by status
        """
        try:
            # Get query parameters for filtering
            status_filter = request.query_params.get('status', None)
            date_from = request.query_params.get('date_from', None)
            date_to = request.query_params.get('date_to', None)
            
            # Build the base query
            query = Q()
            
            # Apply status filter if provided
            if status_filter:
                statuses = status_filter.split(',')
                query &= Q(status__in=statuses)
            
            # Apply date range filters if provided
            if date_from:
                query &= Q(created_at__gte=date_from)
            if date_to:
                query &= Q(created_at__lte=date_to)
            
            # Count bids with the applied filters
            total_bids = Bid.objects.filter(query).count()
            
            # Count bids by status
            status_counts = {}
            for status_choice, _ in Bid.STATUS_CHOICES:
                status_counts[status_choice] = Bid.objects.filter(status=status_choice).count()
            
            # Build the response
            response_data = {
                "total_bids": total_bids,
                "status_counts": status_counts
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve total bids count: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
