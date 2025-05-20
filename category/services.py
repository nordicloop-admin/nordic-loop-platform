from category.repository import CategoryRepository,SubCategoryRepository
from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from typing import Any, Dict, Optional, List
from category.models import Category, SubCategory


logging_service = LoggingService()

class CategoryService:
    def __init__(self, category_repository: CategoryRepository):
        self.repository = category_repository

    def create_category(self, data: Dict[str, Any]) -> Category:
        try:
            category = self.repository.create_category(data).data
            return category
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_category(self, id: int, data: Dict[str, Any]) -> Category:
        try:
            category = self.repository.update_category(id, data).data
            return category
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_category(self, id: int) -> None:
        try:
            self.repository.delete_category(id)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def list_categories(self) -> List[Category]:
        try:
            categories = self.repository.list_categories().data
            return categories
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_category_by_id(self, id: int) -> Optional[Category]:
        try:
            category = self.repository.get_category_by_id(id).data
            return category
        except Exception as e:
            logging_service.log_error(e)
            raise e
    



class SubCategoryService:
    def __init__(self, subcategory_repository: SubCategoryRepository):
        self.repository = subcategory_repository

    def create_subcategory(self, data: Dict[str, Any]) -> SubCategory:
        response = self.repository.create_subcategory(data)
        
        if not response.success or not response.data:
            raise ValueError(response.message)
        
        return response.data


    def update_subcategory(self, id: int, data: Dict[str, Any]) -> SubCategory:
        try:
            subcategory = self.repository.update_subcategory(id, data).data
            return subcategory
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_subcategory(self, id: int) -> None:
        try:
            self.repository.delete_subcategory(id)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def list_subcategories(self) -> List[SubCategory]:
        try:
            subcategories = self.repository.list_subcategories().data
            return subcategories
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_subcategory_by_category(self, category_name: int) -> List[SubCategory]:
        try:
            subcategories = self.repository.get_subcategory_by_category(category_name).data
            return subcategories
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_subcategory_by_id(self, id: int) -> Optional[SubCategory]:
        try:
            subcategory = self.repository.get_subcategory_by_id(id).data
            return subcategory
        except Exception as e:
            logging_service.log_error(e)
            raise e





    
   




