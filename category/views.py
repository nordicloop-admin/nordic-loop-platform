from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from category.repository import CategoryRepository, SubCategoryRepository
from category.services import CategoryService, SubCategoryService
from category.serializers import CategorySerializer, SubCategorySerializer

category_repository = CategoryRepository()
sub_repository = SubCategoryRepository()
category_service = CategoryService(category_repository)
sub_service = SubCategoryService(sub_repository)


class CategoryView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            category = category_service.create_category(request.data)
            serializer = CategorySerializer(category)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, category_id=None):
   
        try:
            if category_id:
                category = category_service.get_category_by_id(category_id)
                if not category:
                    return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
                # Use CategoryDetailSerializer for GET single to show subcategories
                serializer = CategorySerializer(category)
                return Response(serializer.data)
            else:
                categories = category_service.list_categories()
                # Use CategoryDetailSerializer for GET list to show subcategories
                serializer = CategorySerializer(categories, many=True)
                return Response(serializer.data)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, category_id):
        # Update a category
        try:
            category = category_service.get_category_by_id(category_id)
            if not category:
                return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
            updated = category_service.update_category(category_id, request.data)
            # For PUT, returning basic category info is usually fine, or use Detail if needed
            serializer = CategorySerializer(updated)
            return Response(serializer.data)
        except Exception:
            return Response({"error": "Update failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, category_id):
        # Delete a category
        try:
            category = category_service.get_category_by_id(category_id)
            if not category:
                return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
            category_service.delete_category(category)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({"error": "Delete failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        



class SubCategoryView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = request.data
            if not isinstance(data, list):
                return Response({"error": "Expected a list of subcategories"}, status=status.HTTP_400_BAD_REQUEST)
            
            subcategories = sub_service.create_subcategory(data)
            serializer = SubCategorySerializer(subcategories, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, id=None):
        try:
            if id:
                subcategory = sub_service.get_subcategory_by_id(id)
                if subcategory:
                    serializer = SubCategorySerializer(subcategory)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({"error": "Subcategory not found"}, status=status.HTTP_404_NOT_FOUND)
            else:
                # List all subcategories
                subcategories = sub_service.list_subcategories()
                serializer = SubCategorySerializer(subcategories, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, id):
        try:
            # Update a specific subcategory
            subcategory = sub_service.update_subcategory(id, request.data)
            if subcategory:
                serializer = SubCategorySerializer(subcategory)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Subcategory not found"}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        try:
            # Delete a specific subcategory
            result = sub_service.delete_subcategory(id)
            if result:
                return Response({"message": "Subcategory deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Subcategory not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




class SubCategoryByCategoryView(APIView):
    def get(self, request, category_name):
        try:
            subcategories = sub_service.get_subcategory_by_category(category_name)
            if subcategories:
                serializer = SubCategorySerializer(subcategories, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "No subcategories found for this category."}, status=status.HTTP_404_NOT_FOUND)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        






    

    

    
