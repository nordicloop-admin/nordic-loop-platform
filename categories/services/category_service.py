from typing import Dict, Any, Optional, List
from django.utils.text import slugify
from django.db.models import Q
from categories.models import Category
from categories.repositories.category_repository import CategoryRepository
from base.utils.responses import APIResponse
from base.services.logging import LoggingService
from rest_framework import status

logging_service = LoggingService()


class CategoryService:
    """
    Service class for category-related operations.
    This class handles business logic related to categories.
    """

    def __init__(self, category_repository: CategoryRepository):
        self.repository = category_repository

    def create_category(self, user, data):
        """
        Create a new category.

        Args:
            user: The user creating the category
            data: Dictionary containing category data

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            if not user or data is None:
                return APIResponse(
                    success=False,
                    message="Invalid user or data",
                    code=status.HTTP_400_BAD_REQUEST
                )

            required_fields = ["name", "description"]
            missing_fields = logging_service.check_required_fields(data, required_fields)
            if missing_fields:
                return APIResponse(
                    success=False,
                    message=f"Missing required fields: {missing_fields}",
                    code=status.HTTP_400_BAD_REQUEST
                )

            # Get parent ID if provided
            parent_id = None
            if 'parent' in data and data['parent']:
                if isinstance(data['parent'], Category):
                    parent_id = data['parent'].id
                else:
                    parent_id = data['parent']

            # Check if category with same name already exists
            existing_category = self.repository.get_category_by_name(
                name=data.get("name"),
                parent_id=parent_id
            ).data

            if existing_category:
                return APIResponse(
                    success=False,
                    message="Category with the same name already exists under this parent",
                    code=status.HTTP_409_CONFLICT
                )

            # Generate slug if not provided
            if "slug" not in data or not data["slug"]:
                data["slug"] = slugify(data["name"])

            # Check if slug already exists
            existing_slug = self.repository.get_category_by_slug(data["slug"]).data
            if existing_slug:
                return APIResponse(
                    success=False,
                    message=f"Category with slug '{data['slug']}' already exists",
                    code=status.HTTP_409_CONFLICT
                )

            # Create the category
            category = self.repository.create_category(user=user, data=data).data
            return APIResponse(
                success=True,
                data=category,
                code=status.HTTP_201_CREATED
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to create category",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_category_by_id(self, id):
        """
        Get a category by ID.

        Args:
            id: Category's ID

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            category = self.repository.get_category_by_id(id).data
            if category:
                return APIResponse(
                    success=True,
                    data=category,
                    code=status.HTTP_200_OK
                )

            return APIResponse(
                success=False,
                message="Category not found",
                code=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to get category",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_all_categories(self):
        """
        Get all categories.

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            categories = self.repository.get_all_categories().data
            return APIResponse(
                success=True,
                data=categories,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to get categories",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_root_categories(self):
        """
        Get all root categories (categories without a parent).

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            categories = self.repository.get_root_categories().data
            return APIResponse(
                success=True,
                data=categories,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to get root categories",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_subcategories(self, parent_id):
        """
        Get all subcategories of a parent category.

        Args:
            parent_id: Parent category ID

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            categories = self.repository.get_subcategories(parent_id).data
            return APIResponse(
                success=True,
                data=categories,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to get subcategories",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_active_categories(self):
        """
        Get all active categories.

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            categories = self.repository.get_active_categories().data
            return APIResponse(
                success=True,
                data=categories,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to get active categories",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def search_categories(self, query):
        """
        Search for categories.

        Args:
            query: Search query

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            categories = self.repository.search_categories(query).data
            return APIResponse(
                success=True,
                data=categories,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to search categories",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def update_category(self, user, id, data):
        """
        Update a category.

        Args:
            user: The user updating the category
            id: Category ID
            data: Dictionary containing fields to update

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            if not user or not id or data is None:
                return APIResponse(
                    success=False,
                    message="User, category ID, and data are required",
                    code=status.HTTP_400_BAD_REQUEST
                )

            # Check if category exists
            existing_category = self.repository.get_category_by_id(id).data
            if not existing_category:
                return APIResponse(
                    success=False,
                    message="Category not found",
                    code=status.HTTP_404_NOT_FOUND
                )

            # Check if name is being changed and if it already exists
            if "name" in data and data["name"] != existing_category.name:
                parent_id = data.get("parent",
                                      existing_category.parent_id if existing_category.parent else None)
                name_check = self.repository.get_category_by_name(
                    name=data["name"],
                    parent_id=parent_id
                ).data

                if name_check and name_check.id != id:
                    return APIResponse(
                        success=False,
                        message="Category with this name already exists under this parent",
                        code=status.HTTP_409_CONFLICT
                    )

            # Generate slug if name is changed and slug is not provided
            if "name" in data and "slug" not in data:
                data["slug"] = slugify(data["name"])

            # Check if slug is being changed and if it already exists
            if "slug" in data and data["slug"] != existing_category.slug:
                slug_check = self.repository.get_category_by_slug(data["slug"]).data
                if slug_check and slug_check.id != id:
                    return APIResponse(
                        success=False,
                        message=f"Category with slug '{data['slug']}' already exists",
                        code=status.HTTP_409_CONFLICT
                    )

            # Check for circular reference
            if "parent" in data and data["parent"]:
                if str(data["parent"]) == str(id):
                    return APIResponse(
                        success=False,
                        message="A category cannot be its own parent",
                        code=status.HTTP_400_BAD_REQUEST
                    )

                # Check if the new parent is a descendant of this category
                parent_check = self.repository.get_category_by_id(data["parent"]).data
                if parent_check:
                    ancestors = parent_check.get_ancestors()
                    if existing_category in ancestors:
                        return APIResponse(
                            success=False,
                            message="Cannot set a descendant as the parent (circular reference)",
                            code=status.HTTP_400_BAD_REQUEST
                        )

            # Update the category
            updated_category = self.repository.update_category(id=id, user=user, data=data).data
            return APIResponse(
                success=True,
                data=updated_category,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to update category",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete_category(self, user, id):
        """
        Delete a category.

        Args:
            user: The user deleting the category
            id: Category ID

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            if not user or not id:
                return APIResponse(
                    success=False,
                    message="User and category ID are required",
                    code=status.HTTP_400_BAD_REQUEST
                )

            # Check if category exists
            existing_category = self.repository.get_category_by_id(id).data
            if not existing_category:
                return APIResponse(
                    success=False,
                    message="Category not found",
                    code=status.HTTP_404_NOT_FOUND
                )

            # Check if category has subcategories
            subcategories = self.repository.get_subcategories(id).data
            if subcategories:
                return APIResponse(
                    success=False,
                    message="Cannot delete a category that has subcategories. Delete the subcategories first or move them to another parent.",
                    code=status.HTTP_400_BAD_REQUEST
                )

            # Delete the category
            self.repository.delete_category(user=user, id=id)
            return APIResponse(
                success=True,
                message="Category deleted successfully",
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to delete category",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def activate_category(self, user, id):
        """
        Activate a category.

        Args:
            user: The user activating the category
            id: Category ID

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            if not user or not id:
                return APIResponse(
                    success=False,
                    message="User and category ID are required",
                    code=status.HTTP_400_BAD_REQUEST
                )

            # Check if category exists
            existing_category = self.repository.get_category_by_id(id).data
            if not existing_category:
                return APIResponse(
                    success=False,
                    message="Category not found",
                    code=status.HTTP_404_NOT_FOUND
                )

            # Activate the category
            activate_result = self.repository.activate_category(id=id, user=user).data
            return APIResponse(
                success=True,
                data=activate_result,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to activate category",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def deactivate_category(self, user, id):
        """
        Deactivate a category.

        Args:
            user: The user deactivating the category
            id: Category ID

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            if not user or not id:
                return APIResponse(
                    success=False,
                    message="User and category ID are required",
                    code=status.HTTP_400_BAD_REQUEST
                )

            # Check if category exists
            existing_category = self.repository.get_category_by_id(id).data
            if not existing_category:
                return APIResponse(
                    success=False,
                    message="Category not found",
                    code=status.HTTP_404_NOT_FOUND
                )

            # Deactivate the category
            deactivate_result = self.repository.deactivate_category(id=id, user=user).data
            return APIResponse(
                success=True,
                data=deactivate_result,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to deactivate category",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_categories_by_user(self, user):
        """
        Get all categories created by a specific user.

        Args:
            user: The user to retrieve categories for

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            categories = self.repository.get_categories_by_user(user=user).data
            return APIResponse(
                success=True,
                data=categories,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to get categories by user",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_category_with_ancestors(self, id):
        """
        Get a category with its ancestors.

        Args:
            id: Category ID

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            category = self.repository.get_category_by_id(id).data
            if not category:
                return APIResponse(
                    success=False,
                    message="Category not found",
                    code=status.HTTP_404_NOT_FOUND
                )

            ancestors = category.get_ancestors(ascending=False, include_self=True)
            return APIResponse(
                success=True,
                data=ancestors,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to get category with ancestors",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_category_with_descendants(self, id):
        """
        Get a category with its descendants.

        Args:
            id: Category ID

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            category = self.repository.get_category_by_id(id).data
            if not category:
                return APIResponse(
                    success=False,
                    message="Category not found",
                    code=status.HTTP_404_NOT_FOUND
                )

            descendants = category.get_descendants(include_self=True)
            return APIResponse(
                success=True,
                data=descendants,
                code=status.HTTP_200_OK
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to get category with descendants",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create_plastic_categories(self, user):
        """
        Create a set of plastic categories.

        Args:
            user: The user creating the categories

        Returns:
            APIResponse with success status, message, data, and code
        """
        try:
            plastic_data = {
                "name": "Plastic",
                "description": "All things plastic",
                "slug": "plastic",
            }

            plastic = self.create_category(user, plastic_data)
            if not plastic.success:
                return plastic

            subcategories = [
                {"name": "PET (Polyethylene Terephthalate)", "description": "Water bottles, soda bottles",
                 "slug": "pet"},
                {"name": "HDPE (High-Density Polyethylene)", "description": "Milk jugs, detergent bottles",
                 "slug": "hdpe"},
                {"name": "PVC (Polyvinyl Chloride)", "description": "Pipes, vinyl siding", "slug": "pvc"},
                {"name": "LDPE (Low-Density Polyethylene)", "description": "Plastic bags, cling wrap",
                 "slug": "ldpe"},
                {"name": "PP (Polypropylene)", "description": "Food containers, yogurt cups", "slug": "pp"},
                {"name": "PS (Polystyrene)", "description": "Foam cups, takeout containers", "slug": "ps"},
                {"name": "Other Plastics", "description": "Various other plastics", "slug": "other-plastics"},
            ]

            plastic_categories = []
            for subcategory_data in subcategories:
                subcategory_data["parent"] = plastic.data
                subcategory = self.create_category(user, subcategory_data)
                if subcategory.success:
                    plastic_categories.append(subcategory.data)
                else:
                    return subcategory

            return APIResponse(
                success=True,
                message="Plastic categories created successfully",
                data=plastic_categories,
                code=status.HTTP_201_CREATED
            )

        except Exception as e:
            logging_service.log_error(e)
            return APIResponse(
                success=False,
                message="Failed to create plastic categories",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
