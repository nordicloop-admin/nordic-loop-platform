from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from .repository import BidRepository
from .services import BidService
from .serializer import BidSerializer
from .models import Bid
from base.utils.pagination import StandardResultsSetPagination

bid_repository = BidRepository()
bid_service = BidService(bid_repository)


class BidView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            ad_id = request.data.get("ad_id")
            amount = request.data.get("amount")
            volume = request.data.get("volume") 

            if not ad_id or not amount:
                return Response(
                    {"error": "ad_id and amount are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            bid = bid_service.create_bid(
                ad_id=ad_id,
                amount=float(amount),
                user=request.user,
                volume=float(volume) if volume else None
            )

            serializer = BidSerializer(bid)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, bid_id):
        try:
            amount = request.data.get("amount")
            if not amount:
                return Response({"error": "Bid amount is required"}, status=status.HTTP_400_BAD_REQUEST)

            result = bid_service.update_bid(bid_id=bid_id, amount=float(amount), user=request.user)

            if "error" in result:
                return Response({"error": result["error"]}, status=status.HTTP_400_BAD_REQUEST)

            serializer = BidSerializer(result["bid"])
            return Response({
                "message": result["message"],
                "bid": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, bid_id):
        try:
            bid = bid_service.get_bid_by_id(bid_id)
            if not bid:
                return Response({"error": "Bid not found"}, status=status.HTTP_404_NOT_FOUND)

            bid_service.delete_bid(bid_id=bid_id, user=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception:
            return Response({"error": "Delete failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BidDetailView(APIView):
    """Get a specific bid"""
    permission_classes = [IsAuthenticated]

    def get(self, request, bid_id):
        try:
            bid = bid_service.get_bid_by_id(bid_id)
            if not bid:
                return Response({"error": "Bid not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = BidSerializer(bid)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BidListView(ListAPIView):
    """List bids for a specific ad with pagination"""
    serializer_class = BidSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get bids filtered by ad_id"""
        ad_id = self.request.query_params.get("ad_id")
        if not ad_id:
            return Bid.objects.none()
        
        return Bid.objects.filter(ad_id=ad_id).select_related('user', 'ad').order_by('-timestamp')


class UserBidsView(ListAPIView):
    """List current user's bids with pagination"""
    serializer_class = BidSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get current user's bids"""
        return Bid.objects.filter(user=self.request.user).select_related('ad', 'user').order_by('-timestamp')
