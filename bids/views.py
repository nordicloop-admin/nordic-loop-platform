from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .repository import BidRepository
from .services import BidService
from .serializer import (
    BidCreateSerializer, BidListSerializer, BidDetailSerializer, 
    BidUpdateSerializer, BidHistorySerializer, BidStatsSerializer
)
from .models import Bid, BidHistory
from ads.models import Ad
from base.utils.pagination import StandardResultsSetPagination

bid_repository = BidRepository()
bid_service = BidService(bid_repository)


class BidCreateView(APIView):
    """Create a new bid"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = BidCreateSerializer(data=request.data, context={'request': request})
            
            if serializer.is_valid():
                bid = serializer.save()
                response_serializer = BidDetailSerializer(bid)
                return Response({
                    "message": "Bid placed successfully",
                    "bid": response_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "error": "Invalid bid data",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BidUpdateView(APIView):
    """Update an existing bid"""
    permission_classes = [IsAuthenticated]

    def put(self, request, bid_id):
        try:
            bid = get_object_or_404(Bid, id=bid_id, user=request.user)
            serializer = BidUpdateSerializer(bid, data=request.data, partial=True)
            
            if serializer.is_valid():
                updated_bid = serializer.save()
                response_serializer = BidDetailSerializer(updated_bid)
                return Response({
                    "message": "Bid updated successfully",
                    "bid": response_serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                "error": "Invalid update data",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BidDeleteView(APIView):
    """Delete (cancel) a bid"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, bid_id):
        try:
            bid_service.delete_bid(bid_id=bid_id, user=request.user)
            return Response({
                "message": "Bid cancelled successfully"
            }, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({
                "error": str(ve)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({
                "error": "Failed to cancel bid"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BidDetailView(APIView):
    """Get detailed information about a specific bid"""
    permission_classes = [IsAuthenticated]

    def get(self, request, bid_id):
        try:
            bid = bid_service.get_bid_by_id(bid_id)
            if not bid:
                return Response({
                    "error": "Bid not found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = BidDetailSerializer(bid)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception:
            return Response({
                "error": "Something went wrong"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AllBidsListView(ListAPIView):
    """List all bids across the platform (for general browsing)"""
    serializer_class = BidListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get all bids with optional filtering"""
        status_filter = self.request.query_params.get('status')
        ad_id = self.request.query_params.get('ad_id')  # Optional ad_id filter
        
        queryset = Bid.objects.select_related('user', 'ad').order_by('-created_at')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if ad_id:
            try:
                queryset = queryset.filter(ad_id=int(ad_id))
            except (ValueError, TypeError):
                pass
        
        return queryset

    def get(self, request, *args, **kwargs):
        """Override to add general statistics"""
        try:
            response = super().get(request, *args, **kwargs)
            
            # Add general bid statistics
            total_bids = Bid.objects.count()
            active_bids = Bid.objects.filter(status__in=['active', 'winning']).count()
            
            response.data['platform_statistics'] = {
                'total_bids': total_bids,
                'active_bids': active_bids,
                'total_bidders': Bid.objects.values('user').distinct().count()
            }
            
            return response
            
        except Exception as e:
            return Response({
                "error": "Failed to retrieve bids"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdBidsListView(ListAPIView):
    """List all bids for a specific ad"""
    serializer_class = BidListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        ad_id = self.kwargs.get('ad_id')
        status_filter = self.request.query_params.get('status')
        
        if not ad_id:
            return Bid.objects.none()
        
        queryset = Bid.objects.filter(ad_id=ad_id).select_related('user', 'ad').order_by('-bid_price_per_unit', '-created_at')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

    def get(self, request, *args, **kwargs):
        try:
            ad_id = kwargs.get('ad_id')
            ad = get_object_or_404(Ad, id=ad_id)
            
            response = super().get(request, *args, **kwargs)
            
            # Add bid statistics to response
            stats = bid_service.get_bid_statistics(ad_id)
            response.data['bid_statistics'] = stats
            response.data['ad_info'] = {
                'id': ad.id,
                'title': ad.title,
                'starting_bid_price': ad.starting_bid_price,
                'reserve_price': ad.reserve_price,
                'available_quantity': ad.available_quantity,
                'currency': ad.currency,
                'auction_end_date': ad.auction_end_date
            }
            
            return response
            
        except Exception as e:
            return Response({
                "error": "Failed to retrieve bids for this ad"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserBidsListView(ListAPIView):
    """List current user's bids"""
    serializer_class = BidListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        status_filter = self.request.query_params.get('status')
        queryset = Bid.objects.filter(user=self.request.user).select_related('ad', 'user').order_by('-created_at')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class BidHistoryView(ListAPIView):
    """Get bid history for a specific bid"""
    serializer_class = BidHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        bid_id = self.kwargs.get('bid_id')
        return BidHistory.objects.filter(bid_id=bid_id).order_by('-timestamp')

    def get(self, request, *args, **kwargs):
        try:
            bid_id = kwargs.get('bid_id')
            bid = get_object_or_404(Bid, id=bid_id)
            
            # Check if user has permission to view this bid history
            if bid.user != request.user and bid.ad.user != request.user:
                return Response({
                    "error": "You don't have permission to view this bid history"
                }, status=status.HTTP_403_FORBIDDEN)
            
            return super().get(request, *args, **kwargs)
            
        except Exception:
            return Response({
                "error": "Failed to retrieve bid history"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdBidStatsView(APIView):
    """Get comprehensive bid statistics for an ad"""
    permission_classes = [IsAuthenticated]

    def get(self, request, ad_id):
        try:
            ad = get_object_or_404(Ad, id=ad_id)
            stats = bid_service.get_bid_statistics(ad_id)
            
            # Add current highest bid info
            highest_bid = bid_service.get_highest_bid_for_ad(ad_id)
            if highest_bid:
                stats['current_highest_bid'] = {
                    'bid_price_per_unit': highest_bid.bid_price_per_unit,
                    'total_bid_value': highest_bid.total_bid_value,
                    'volume_requested': highest_bid.volume_requested,
                    'bidder': highest_bid.user.username,
                    'timestamp': highest_bid.created_at
                }
            else:
                stats['current_highest_bid'] = None
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception:
            return Response({
                "error": "Failed to retrieve bid statistics"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BidSearchView(ListAPIView):
    """Search and filter bids across the platform"""
    serializer_class = BidListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Bid.objects.select_related('user', 'ad').order_by('-created_at')
        
        # Filter parameters
        ad_title = self.request.query_params.get('ad_title')
        material_category = self.request.query_params.get('category')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        bid_status = self.request.query_params.get('status')
        user_id = self.request.query_params.get('user_id')
        
        if ad_title:
            queryset = queryset.filter(ad__title__icontains=ad_title)
        
        if material_category:
            queryset = queryset.filter(ad__category__name__icontains=material_category)
        
        if min_price:
            try:
                queryset = queryset.filter(bid_price_per_unit__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(bid_price_per_unit__lte=float(max_price))
            except ValueError:
                pass
        
        if bid_status:
            queryset = queryset.filter(status=bid_status)
        
        if user_id:
            try:
                queryset = queryset.filter(user_id=int(user_id))
            except ValueError:
                pass
        
        return queryset


class WinningBidsView(ListAPIView):
    """Get all winning bids for the current user"""
    serializer_class = BidListSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bid.objects.filter(
            user=self.request.user,
            status__in=['winning', 'won']
        ).select_related('ad', 'user').order_by('-created_at')


class CloseAuctionView(APIView):
    """Close an auction (for ad owners only)"""
    permission_classes = [IsAuthenticated]

    def post(self, request, ad_id):
        try:
            ad = get_object_or_404(Ad, id=ad_id, user=request.user)
            
            result = bid_service.close_auction(ad_id)
            
            if result.get('success'):
                return Response({
                    "message": result['message'],
                    "winning_bid_id": result.get('winning_bid').id if result.get('winning_bid') else None,
                    "final_price": result.get('final_price'),
                    "volume": result.get('volume')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": result['message'],
                    "details": {
                        "reserve_price": result.get('reserve_price'),
                        "highest_bid": result.get('highest_bid')
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception:
            return Response({
                "error": "Failed to close auction"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Legacy view for backward compatibility
class BidView(APIView):
    """Legacy bid view - redirects to new endpoints"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Legacy create bid endpoint"""
        return BidCreateView.as_view()(request)

    def put(self, request, bid_id):
        """Legacy update bid endpoint"""
        return BidUpdateView.as_view()(request, bid_id)

    def delete(self, request, bid_id):
        """Legacy delete bid endpoint"""
        return BidDeleteView.as_view()(request, bid_id)
