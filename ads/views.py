from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import  IsAuthenticated
from ads.repository import AdRepository
from ads.services import AdService
from ads.serializer import AdSerializer

ad_repository = AdRepository()
ad_service = AdService(ad_repository)

class AdView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            ad = ad_service.create_ad(request.data, request.FILES, request.user)
            serializer = AdSerializer(ad)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, ad_id=None):
        try:
            if ad_id:
                ad = ad_service.get_ad_by_id(ad_id)
                if not ad:
                    return Response({"error": "Ad not found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = AdSerializer(ad)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                ads = ad_service.list_ads()
                serializer = AdSerializer(ads, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, ad_id):
        try:
            updated = ad_service.update_ad(ad_id, request.data)
            serializer = AdSerializer(updated)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Update failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, ad_id):
        try:
            ad = ad_service.get_ad_by_id(ad_id)
            if not ad:
                return Response({"error": "Ad not found"}, status=status.HTTP_404_NOT_FOUND)
            ad_service.delete_ad(ad_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({"error": "Delete failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
