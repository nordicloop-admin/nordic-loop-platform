from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from django.db.models import Q
from category.models import Category, SubCategory
from category.serializers import SubCategorySerializer

logging_service = LoggingService()

class CategoryRepository:
    def create_category(self, data) -> RepositoryResponse:
        try:
            name = data.pop("name", None)
            if not name:
                return RepositoryResponse(
                    success=False,
                    message="Category name is required",
                    data=None,
                )

            category = Category.objects.create(name=name)

            return RepositoryResponse(
                success=True,
                message="Category created successfully",
                data=category,
            )

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to create category",
                data=None,
            )



    def update_category(self, id, data) -> RepositoryResponse:
        try:
            category = Category.objects.get(id=id)
            for key, value in data.items():
                setattr(category, key, value)
            category.save()
            return RepositoryResponse(
                success=True,
                message="category updated successfully",
                data=category,
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="category not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to update category",
                data=None,
            )
    


    def delete_category(self, id) -> RepositoryResponse:
        try:
            category = Category.objects.get(id=id)
            category.delete()
            return RepositoryResponse(
                success=True,
                message="category deleted successfully",
                data=None,
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="category not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to delete category",
                data=None,
            )
    


    def list_categories(self) -> RepositoryResponse:
        try:
            category = Category.objects.all()
            return RepositoryResponse(
                success=True,
                message="category found",
                data=category,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get category",
                data=None,
            )
        
    
    def get_category_by_id(self, id) -> RepositoryResponse:
        try:
            category = Category.objects.get(id=id)
            return RepositoryResponse(
                success=True,
                message="category found",
                data=category,
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="category not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get category",
                data=None,
            )

        


class SubCategoryRepository:

    def create_subcategory(self, data_list) -> RepositoryResponse:
        try:
            created_subcategories = []

            for data in data_list:
                if not isinstance(data, dict):
                    return RepositoryResponse(
                success=False,
                message="Please complete the list ",
                data=None,
            )

                category_name = data.pop("category_name", None)

                if not category_name:
                    return RepositoryResponse(
                        success=False,
                        message="No such Catgeory found",
                        data=None,
                    )

                try:
                    category = Category.objects.get(name=category_name)
                    subcategory = SubCategory.objects.create(category=category, **data)
                    created_subcategories.append(subcategory)
                except Category.DoesNotExist:
                    continue

            return RepositoryResponse(
                success=True,
                message=f"{len(created_subcategories)} SubCategories created successfully",
                data=created_subcategories,
            )

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to create subcategories",
                data=None,
            )



    
    def get_subcategory_by_id(self, id, data) -> RepositoryResponse:
        try:
            subcategory = SubCategory.objects.get(pk=id)
            serializer = SubCategorySerializer(subcategory, data=data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return RepositoryResponse(success=True, data=serializer.data)

            return RepositoryResponse(success=False, error=serializer.errors)

        except SubCategory.DoesNotExist:
            return RepositoryResponse(success=False, error="Subcategory not found")
        except Exception as e:
            return RepositoryResponse(success=False, error=str(e))
        


    def update_subcategory(self, id, data) -> RepositoryResponse:
        try:
            subcategory = SubCategory.objects.get(id=id)
            for key, value in data.items():
                setattr(subcategory, key, value)
            subcategory.save()
            return RepositoryResponse(
                success=True,
                message="SubCategory updated successfully",
                data=subcategory,
            )
        except SubCategory.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="SubCategory not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to update subcategory",
                data=None,
            )

    def delete_subcategory(self, id) -> RepositoryResponse:
        try:
            subcategory = SubCategory.objects.get(id=id)
            subcategory.delete()
            return RepositoryResponse(
                success=True,
                message="SubCategory deleted successfully",
                data=None,
            )
        except SubCategory.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="SubCategory not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to delete subcategory",
                data=None,
            )

    def list_subcategories(self) -> RepositoryResponse:
        try:
            subcategories = SubCategory.objects.all()
            return RepositoryResponse(
                success=True,
                message="SubCategories found",
                data=subcategories,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get subcategories",
                data=None,
            )

    def get_subcategory_by_category(self, category_name) -> RepositoryResponse:
        try:
            category = Category.objects.get(name=category_name)
            subcategories = category.subcategories.all()
            return RepositoryResponse(
                success=True,
                message="SubCategories found",
                data=subcategories,
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get subcategories",
                data=None,
            )
        
    
   
        