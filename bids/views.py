from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .repository import BidRepository
from .services import BidService
from .serializer import BidSerializer

bid_repository = BidRepository()
bid_service = BidService(bid_repository)


class BidView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            ad_id = request.data.get("ad_id")
            amount = request.data.get("amount")

            if not ad_id or not amount:
                return Response({"error": "ad_id and amount are required"}, status=status.HTTP_400_BAD_REQUEST)

            bid = bid_service.create_bid(ad_id=ad_id, amount=amount, user=request.user)

            if isinstance(bid, dict) and "error" in bid:
                return Response({"error": bid["error"]}, status=status.HTTP_400_BAD_REQUEST)

            serializer = BidSerializer(bid)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def get(self, request, bid_id=None):
        try:
            if bid_id:
                bid = bid_service.get_bid_by_id(bid_id)
                if not bid:
                    return Response({"error": "Bid not found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = BidSerializer(bid)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                ad_id = request.query_params.get("ad_id")
                bids = bid_service.list_bids(ad_id=ad_id, user=request.user)
                return Response(bids, status=status.HTTP_200_OK)  # Already serialized

        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def put(self, request, bid_id):
        try:
            amount = request.data.get("amount")
            if not amount:
                return Response({"error": "Bid amount is required"}, status=status.HTTP_400_BAD_REQUEST)

            bid = bid_service.update_bid(bid_id=bid_id, amount=amount, user=request.user)
            serializer = BidSerializer(bid)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Update failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, bid_id):
        try:
            bid = bid_service.get_bid_by_id(bid_id)
            if not bid:
                return Response({"error": "Bid not found"}, status=status.HTTP_404_NOT_FOUND)

            bid_service.delete_bid(bid_id=bid_id, user=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Exception:
            return Response({"error": "Delete failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
