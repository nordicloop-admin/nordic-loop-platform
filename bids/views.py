from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.db.models import Q
from django.shortcuts import get_object_or_404
from decimal import Decimal

from .repository import BidRepository
from .services import BidService
from .serializer import (
    BidCreateSerializer, BidListSerializer, BidDetailSerializer, 
    BidUpdateSerializer, BidHistorySerializer, BidStatsSerializer,
    AdminBidListSerializer, AdminBidDetailSerializer
)
from .models import Bid, BidHistory
from ads.models import Ad
from base.utils.pagination import StandardResultsSetPagination
from users.models import User

# Initialize repository and service
bid_repository = BidRepository()
bid_service = BidService(bid_repository)


class BidCreateView(APIView):
    """Create a new bid"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Place a bid on an ad"""
        try:
            serializer = BidCreateSerializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                bid = serializer.save()
                
                # Return the saved bid using BidDetailSerializer
                response_serializer = BidDetailSerializer(bid)
                return Response(
                    {
                        "message": "Bid placed successfully",
                        "bid": response_serializer.data
                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {"error": "Validation failed", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"error": f"Failed to place bid: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BidUpdateView(APIView):
    """Update an existing bid"""
    permission_classes = [IsAuthenticated]

    def put(self, request, bid_id):
        """Update a bid completely"""
        try:
            bid = get_object_or_404(Bid, id=bid_id, user=request.user)
            
            serializer = BidUpdateSerializer(bid, data=request.data, partial=False)
            if serializer.is_valid():
                updated_bid = serializer.save()
                
                response_serializer = BidDetailSerializer(updated_bid)
                return Response(
                    {
                        "message": "Bid updated successfully",
                        "bid": response_serializer.data
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Validation failed", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"error": f"Failed to update bid: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, bid_id):
        """Partially update a bid"""
        try:
            bid = get_object_or_404(Bid, id=bid_id, user=request.user)
            
            serializer = BidUpdateSerializer(bid, data=request.data, partial=True)
            if serializer.is_valid():
                updated_bid = serializer.save()
                
                response_serializer = BidDetailSerializer(updated_bid)
                return Response(
                    {
                        "message": "Bid updated successfully",
                        "bid": response_serializer.data
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Validation failed", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {"error": f"Failed to update bid: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BidDeleteView(APIView):
    """Delete (cancel) a bid"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, bid_id):
        """Cancel a bid"""
        try:
            bid_service.delete_bid(bid_id, request.user)
            return Response(
                {"message": "Bid cancelled successfully"},
                status=status.HTTP_200_OK
            )
        except ValueError as ve:
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to cancel bid: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BidDetailView(APIView):
    """Get bid details"""
    permission_classes = [IsAuthenticated]

    def get(self, request, bid_id):
        """Get detailed information about a specific bid"""
        try:
            bid = bid_service.get_bid_by_id(bid_id)
            if not bid:
                return Response(
                    {"error": "Bid not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user can view this bid (owner, ad owner, or admin)
            if (bid.user != request.user and 
                bid.ad.user != request.user and 
                not request.user.is_staff):
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = BidDetailSerializer(bid)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve bid: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AllBidsListView(APIView):
    """List all bids on the platform (admin/public view)"""
    permission_classes = [AllowAny]

    def get(self, request):
        """Get all bids with optional filtering"""
        try:
            # Get query parameters
            status_filter = request.query_params.get('status')
            ad_id = request.query_params.get('ad_id')
            
            bids = Bid.objects.select_related('user', 'ad').all()
            
            # Apply filters
            if status_filter:
                bids = bids.filter(status=status_filter)
            
            if ad_id:
                bids = bids.filter(ad_id=ad_id)
            
            bids = bids.order_by('-created_at')
            
            serializer = BidListSerializer(bids, many=True)
            return Response(
                {"bids": serializer.data},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve bids: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdBidsListView(APIView):
    """List all bids for a specific ad"""
    permission_classes = [AllowAny]

    def get(self, request, ad_id):
        """Get all bids for a specific ad"""
        try:
            # Verify ad exists
            ad = get_object_or_404(Ad, id=ad_id)

            status_filter = request.query_params.get('status')
            bids = bid_service.get_bids_for_ad(ad_id, status_filter)

            serializer = BidListSerializer(bids, many=True)
            return Response(
                {
                    "ad_id": ad_id,
                    "ad_title": ad.title,
                    "total_bids": len(bids),
                    "bids": serializer.data
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve bids: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdBidHistoryView(APIView):
    """Get detailed bid history for an ad with company information"""
    permission_classes = [AllowAny]

    def get(self, request, ad_id):
        """Get chronological bid history for an ad"""
        try:
            from ads.models import Ad
            from company.models import Company

            # Verify ad exists
            ad = get_object_or_404(Ad, id=ad_id)

            # Get all bids for this ad, ordered by creation time (newest first)
            bids = Bid.objects.filter(ad_id=ad_id).select_related(
                'user', 'user__company'
            ).order_by('-created_at')

            bid_history = []
            for bid in bids:
                # Get company name
                company_name = "Unknown Company"
                if bid.user and bid.user.company:
                    company_name = bid.user.company.official_name or bid.user.company.trading_name
                elif bid.user:
                    company_name = f"{bid.user.first_name} {bid.user.last_name}".strip() or bid.user.email

                bid_history.append({
                    "id": bid.id,
                    "company_name": company_name,
                    "bid_amount": str(bid.bid_price_per_unit),
                    "total_value": str(bid.total_bid_value) if bid.total_bid_value else str(bid.bid_price_per_unit * bid.volume_requested),
                    "volume_requested": str(bid.volume_requested),
                    "volume_type": bid.volume_type,
                    "currency": ad.currency,
                    "status": bid.status,
                    "created_at": bid.created_at.isoformat(),
                    "notes": bid.notes or ""
                })

            return Response(
                {
                    "ad_id": ad_id,
                    "ad_title": ad.title,
                    "total_bids": len(bid_history),
                    "bid_history": bid_history
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve bid history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserBidsListView(APIView):
    """List current user's bids"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's bids"""
        try:
            status_filter = request.query_params.get('status')
            bids = bid_service.get_user_bids(request.user, status_filter)
            
            serializer = BidListSerializer(bids, many=True)
            return Response(
                {
                    "user_id": request.user.id,
                    "total_bids": len(bids),
                    "bids": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve user bids: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WinningBidsView(APIView):
    """Get user's winning bids"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user's winning bids"""
        try:
            winning_bids = Bid.objects.filter(
                user=request.user,
                status__in=['winning', 'won']
            ).select_related('ad').order_by('-created_at')
            
            serializer = BidListSerializer(winning_bids, many=True)
            return Response(
                {
                    "user_id": request.user.id,
                    "winning_bids_count": len(winning_bids),
                    "winning_bids": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve winning bids: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdBidStatsView(APIView):
    """Get bid statistics for an ad"""
    permission_classes = [AllowAny]

    def get(self, request, ad_id):
        """Get comprehensive bid statistics for an ad"""
        try:
            # Verify ad exists
            get_object_or_404(Ad, id=ad_id)
            
            stats = bid_service.get_bid_statistics(ad_id)
            serializer = BidStatsSerializer(stats)
            
            return Response(
                {
                    "ad_id": ad_id,
                    "statistics": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve bid statistics: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BidHistoryView(APIView):
    """Get bid modification history"""
    permission_classes = [IsAuthenticated]

    def get(self, request, bid_id):
        """Get history of changes for a specific bid"""
        try:
            bid = get_object_or_404(Bid, id=bid_id)
            
            # Check permissions
            if (bid.user != request.user and 
                bid.ad.user != request.user and 
                not request.user.is_staff):
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            history = BidHistory.objects.filter(bid=bid).order_by('-timestamp')
            serializer = BidHistorySerializer(history, many=True)
            
            return Response(
                {
                    "bid_id": bid_id,
                    "history": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve bid history: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BidSearchView(APIView):
    """Advanced bid search"""
    permission_classes = [AllowAny]

    def get(self, request):
        """Search bids with advanced filters"""
        try:
            filters = {}
            
            # Extract search parameters
            if request.query_params.get('status'):
                filters['status'] = request.query_params.get('status')
            
            if request.query_params.get('ad_id'):
                filters['ad_id'] = int(request.query_params.get('ad_id'))
            
            if request.query_params.get('user_id'):
                filters['user_id'] = int(request.query_params.get('user_id'))
            
            if request.query_params.get('min_price'):
                filters['min_price'] = float(request.query_params.get('min_price'))
            
            if request.query_params.get('max_price'):
                filters['max_price'] = float(request.query_params.get('max_price'))
            
            if request.query_params.get('keyword'):
                filters['keyword'] = request.query_params.get('keyword')
            
            bids = bid_repository.search_bids(filters)
            serializer = BidListSerializer(bids, many=True)
            
            return Response(
                {
                    "filters_applied": filters,
                    "results_count": len(bids),
                    "bids": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": f"Search failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CloseAuctionView(APIView):
    """Close auction for an ad (admin only)"""
    permission_classes = [IsAdminUser]

    def post(self, request, ad_id):
        """Close auction and determine winner"""
        try:
            result = bid_service.close_auction(ad_id)
            
            if result["success"]:
                return Response(result, status=status.HTTP_200_OK)
            else:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response(
                {"error": f"Failed to close auction: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminBidListView(APIView):
    """
    Admin endpoint for listing bids with filtering and pagination
    GET /api/bids/admin/bids/
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
                valid_statuses = ['active', 'outbid', 'winning', 'won', 'lost', 'cancelled']
                if status_filter not in valid_statuses:
                    return Response(
                        {"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Get filtered bids
            pagination_data = bid_service.get_admin_bids_filtered(
                search=search,
                status=status_filter,
                page=page,
                page_size=page_size
            )

            # Serialize the results
            serializer = AdminBidListSerializer(pagination_data['results'], many=True)
            
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
                    "error": "Failed to retrieve bids",
                    "details": str(e),
                    "traceback": error_details
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminBidDetailView(APIView):
    """
    Admin endpoint for retrieving a specific bid
    GET /api/bids/admin/bids/{id}/
    """
    permission_classes = [IsAdminUser]

    def get(self, request, bid_id):
        try:
            bid = bid_service.get_bid_by_id(bid_id)
            if not bid:
                return Response(
                    {"error": "Bid not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = AdminBidDetailSerializer(bid)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Failed to retrieve bid"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Legacy View (for backward compatibility)
class BidView(APIView):
    """Legacy bid view for backward compatibility"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Legacy create bid endpoint"""
        return BidCreateView.as_view()(request)

    def put(self, request, bid_id):
        """Legacy update bid endpoint"""
        try:
            bid_price = request.data.get('bid_price_per_unit')
            volume = request.data.get('volume_requested')
            notes = request.data.get('notes')
            
            updated_bid = bid_service.update_bid(
                bid_id=bid_id,
                bid_price_per_unit=bid_price,
                volume_requested=volume,
                notes=notes,
                user=request.user
            )
            
            serializer = BidDetailSerializer(updated_bid)
            return Response(
                {
                    "message": "Bid updated successfully",
                    "bid": serializer.data
                },
                status=status.HTTP_200_OK
            )
            
        except ValueError as ve:
            return Response(
                {"error": str(ve)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to update bid: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, bid_id):
        """Legacy delete bid endpoint"""
        return BidDeleteView.as_view()(request, bid_id)


class AdminBidApproveView(APIView):
    """
    Admin endpoint for approving a bid
    POST /api/bids/admin/bids/{id}/approve/
    """
    permission_classes = [IsAdminUser]

    def post(self, request, bid_id):
        try:
            result = bid_service.admin_approve_bid(bid_id, request.user)
            
            if not result["success"]:
                return Response(
                    {"error": result["message"]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            return Response(
                {"message": result["message"]},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": "Failed to approve bid"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminBidRejectView(APIView):
    """
    Admin endpoint for rejecting a bid
    POST /api/bids/admin/bids/{id}/reject/
    """
    permission_classes = [IsAdminUser]

    def post(self, request, bid_id):
        try:
            result = bid_service.admin_reject_bid(bid_id, request.user)
            
            if not result["success"]:
                return Response(
                    {"error": result["message"]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            return Response(
                {"message": result["message"]},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": "Failed to reject bid"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminBidMarkAsWonView(APIView):
    """
    Admin endpoint for marking a bid as won
    POST /api/bids/admin/bids/{id}/mark-as-won/
    """
    permission_classes = [IsAdminUser]

    def post(self, request, bid_id):
        try:
            result = bid_service.admin_mark_bid_as_won(bid_id, request.user)
            
            if not result["success"]:
                return Response(
                    {"error": result["message"]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            return Response(
                {"message": result["message"]},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"error": "Failed to mark bid as won"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
