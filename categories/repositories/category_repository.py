from typing import Dict, Any, Optional, List
from django.db.models import Q
from categories.models import Category
from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService

logging_service = LoggingService()


class CategoryRepository:
    """
    Repository class for category-related database operations.
    """

    def create_category(self, user, data) -> RepositoryResponse:
        """
        Create a new category.

        Args:
            user: The user creating the category
            data: Dictionary containing category data

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            data['created_by'] = user
            category = Category.objects.create(**data)
            return RepositoryResponse(
                success=True,
                message="Category created successfully",
                data=category
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to create category",
                data=None
            )

    def get_category_by_id(self, id) -> RepositoryResponse:
        """
        Get a category by ID.

        Args:
            id: Category's ID

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            category = Category.objects.select_related('parent', 'created_by').get(id=id, is_deleted=False)
            return RepositoryResponse(
                success=True,
                message="Category found",
                data=category
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get category",
                data=None
            )

    def get_category_by_name(self, name, parent_id=None) -> RepositoryResponse:
        """
        Get a category by name and optional parent.

        Args:
            name: Category's name
            parent_id: Parent category ID (optional)

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            query = {'name': name, 'is_deleted': False}
            if parent_id is not None:
                query['parent_id'] = parent_id
            else:
                query['parent'] = None

            category = Category.objects.select_related('parent', 'created_by').get(**query)
            return RepositoryResponse(
                success=True,
                message="Category found",
                data=category
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get category",
                data=None
            )

    def get_category_by_slug(self, slug) -> RepositoryResponse:
        """
        Get a category by slug.

        Args:
            slug: Category's slug

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            category = Category.objects.select_related('parent', 'created_by').get(slug=slug, is_deleted=False)
            return RepositoryResponse(
                success=True,
                message="Category found",
                data=category
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get category",
                data=None
            )

    def get_all_categories(self) -> RepositoryResponse:
        """
        Get all categories.

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            categories = Category.objects.select_related('parent', 'created_by').filter(is_deleted=False).order_by('name')
            return RepositoryResponse(
                success=True,
                message="Categories retrieved successfully",
                data=categories
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to retrieve categories",
                data=None
            )

    def get_root_categories(self) -> RepositoryResponse:
        """
        Get all root categories (categories without a parent).

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            categories = Category.objects.select_related('created_by').filter(parent=None, is_deleted=False).order_by('name')
            return RepositoryResponse(
                success=True,
                message="Root categories retrieved successfully",
                data=categories
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to retrieve root categories",
                data=None
            )

    def get_subcategories(self, parent_id) -> RepositoryResponse:
        """
        Get all subcategories of a parent category.

        Args:
            parent_id: Parent category ID

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            categories = Category.objects.select_related('parent', 'created_by').filter(parent_id=parent_id, is_deleted=False).order_by('name')
            return RepositoryResponse(
                success=True,
                message="Subcategories retrieved successfully",
                data=categories
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to retrieve subcategories",
                data=None
            )

    def get_active_categories(self) -> RepositoryResponse:
        """
        Get all active categories.

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            categories = Category.objects.select_related('parent', 'created_by').filter(is_active=True, is_deleted=False).order_by('name')
            return RepositoryResponse(
                success=True,
                message="Active categories retrieved successfully",
                data=categories
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to retrieve active categories",
                data=None
            )

    def search_categories(self, query) -> RepositoryResponse:
        """
        Search for categories.

        Args:
            query: Search query

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            categories = Category.objects.select_related('parent', 'created_by').filter(
                Q(name__icontains=query) |
                Q(slug__icontains=query) |
                Q(description__icontains=query),
                is_deleted=False
            ).order_by('name')

            return RepositoryResponse(
                success=True,
                message="Categories found",
                data=categories
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to search categories",
                data=None
            )

    def update_category(self, id, user, data) -> RepositoryResponse:
        """
        Update a category.

        Args:
            id: Category ID
            user: The user updating the category
            data: Dictionary containing fields to update

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            category = Category.objects.select_related('parent', 'created_by').get(id=id, is_deleted=False)

            for key, value in data.items():
                setattr(category, key, value)

            category.save()
            return RepositoryResponse(
                success=True,
                message="Category updated successfully",
                data=category
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to update category",
                data=None
            )

    def delete_category(self, user, id) -> RepositoryResponse:
        """
        Soft delete a category.

        Args:
            user: The user deleting the category
            id: Category ID

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            category = Category.objects.get(id=id, is_deleted=False)
            category.is_deleted = True
            category.save()
            return RepositoryResponse(
                success=True,
                message="Category deleted successfully",
                data=None
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to delete category",
                data=None
            )

    def activate_category(self, id, user) -> RepositoryResponse:
        """
        Activate a category.

        Args:
            id: Category ID
            user: The user activating the category

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            category = Category.objects.get(id=id, is_deleted=False)
            category.is_active = True
            category.save()
            return RepositoryResponse(
                success=True,
                message="Category activated successfully",
                data=category
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to activate category",
                data=None
            )

    def deactivate_category(self, id, user) -> RepositoryResponse:
        """
        Deactivate a category.

        Args:
            id: Category ID
            user: The user deactivating the category

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            category = Category.objects.get(id=id, is_deleted=False)
            category.is_active = False
            category.save()
            return RepositoryResponse(
                success=True,
                message="Category deactivated successfully",
                data=category
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to deactivate category",
                data=None
            )

    def get_category_with_ancestors(self, id) -> RepositoryResponse:
        """
        Get a category with its ancestors.

        Args:
            id: Category ID

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            category = Category.objects.select_related('parent', 'created_by').get(id=id, is_deleted=False)
            ancestors = category.get_ancestors()

            return RepositoryResponse(
                success=True,
                message="Category and ancestors retrieved successfully",
                data={
                    'category': category,
                    'ancestors': ancestors
                }
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to retrieve category with ancestors",
                data=None
            )

    def get_category_with_descendants(self, id) -> RepositoryResponse:
        """
        Get a category with its descendants.

        Args:
            id: Category ID

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            category = Category.objects.select_related('parent', 'created_by').get(id=id, is_deleted=False)
            descendants = category.get_descendants()

            return RepositoryResponse(
                success=True,
                message="Category and descendants retrieved successfully",
                data={
                    'category': category,
                    'descendants': descendants
                }
            )
        except Category.DoesNotExist:
            return RepositoryResponse(
                success=False,
                message="Category not found",
                data=None
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to retrieve category with descendants",
                data=None
            )

    def get_categories_by_user(self, user) -> RepositoryResponse:
        """
        Get all categories created by a user.

        Args:
            user: The user who created the categories

        Returns:
            RepositoryResponse with success status, message, and data
        """
        try:
            categories = Category.objects.select_related('parent', 'created_by').filter(created_by=user, is_deleted=False).order_by('name')
            return RepositoryResponse(
                success=True,
                message="Categories retrieved successfully",
                data=categories
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to retrieve categories",
                data=None
            )
