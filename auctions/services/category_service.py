from typing import Dict, Any, Optional, List
from auctions.models import Category
from auctions.repositories.category_repository import CategoryRepository
from base.services.logging import LoggingService

logging_service = LoggingService()


class CategoryService:
    """
    Service class for category-related operations.
    This class handles business logic related to categories.
    """

    def __init__(self, category_repository: CategoryRepository):
        self.repository = category_repository

    def create_category(self, category_data: Dict[str, Any]) -> Category:
        """
        Create a new category.

        Args:
            category_data: Dictionary containing category data

        Returns:
            The created category object

        Raises:
            ValueError: If the category name already exists
        """
        try:
            # Check if category name already exists
            name = category_data.get('name')
            if name:
                existing_category = self.repository.get_category_by_name(name).data
                if existing_category:
                    raise ValueError(f"Category with name '{name}' already exists")

            # Create the category
            category = self.repository.create_category(category_data).data
            return category
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """
        Get a category by ID.

        Args:
            category_id: Category's ID

        Returns:
            The category object if found, None otherwise
        """
        try:
            category = self.repository.get_category_by_id(category_id).data
            return category
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_category_by_name(self, name: str) -> Optional[Category]:
        """
        Get a category by name.

        Args:
            name: Category's name

        Returns:
            The category object if found, None otherwise
        """
        try:
            category = self.repository.get_category_by_name(name).data
            return category
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_all_categories(self) -> List[Category]:
        """
        Get all categories.

        Returns:
            List of all categories
        """
        try:
            categories = self.repository.get_all_categories().data
            return categories
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_active_categories(self) -> List[Category]:
        """
        Get all active categories.

        Returns:
            List of active categories
        """
        try:
            categories = self.repository.get_active_categories().data
            return categories
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_category(self, category: Category, **kwargs) -> Category:
        """
        Update a category.

        Args:
            category: The category to update
            **kwargs: Fields to update

        Returns:
            The updated category object

        Raises:
            ValueError: If the category name already exists
        """
        try:
            # Check if category name already exists
            name = kwargs.get('name')
            if name and name != category.name:
                existing_category = self.repository.get_category_by_name(name).data
                if existing_category:
                    raise ValueError(f"Category with name '{name}' already exists")

            # Update the category
            category = self.repository.update_category(category.id, kwargs).data
            return category
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_category(self, category: Category) -> None:
        """
        Delete a category.

        Args:
            category: The category to delete

        Raises:
            ValueError: If the category has auctions
        """
        try:
            # Check if category has auctions
            if category.auctions.exists():
                raise ValueError("Cannot delete a category that has auctions")

            # Delete the category
            self.repository.delete_category(category.id)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def activate_category(self, category: Category) -> Category:
        """
        Activate a category.

        Args:
            category: The category to activate

        Returns:
            The activated category object
        """
        try:
            category = self.repository.activate_category(category.id).data
            return category
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def deactivate_category(self, category: Category) -> Category:
        """
        Deactivate a category.

        Args:
            category: The category to deactivate

        Returns:
            The deactivated category object
        """
        try:
            category = self.repository.deactivate_category(category.id).data
            return category
        except Exception as e:
            logging_service.log_error(e)
            raise e
