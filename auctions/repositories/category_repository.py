from typing import Dict, Any, Optional, List
from auctions.models import Category


class CategoryRepository:
    """
    Repository class for category-related database operations.
    """
    
    @staticmethod
    def create_category(category_data: Dict[str, Any]) -> Category:
        """
        Create a new category.
        
        Args:
            category_data: Dictionary containing category data
            
        Returns:
            The created category object
        """
        category = Category(**category_data)
        category.save()
        return category
    
    @staticmethod
    def get_category_by_id(category_id: int) -> Optional[Category]:
        """
        Get a category by ID.
        
        Args:
            category_id: Category's ID
            
        Returns:
            The category object if found, None otherwise
        """
        try:
            return Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return None
    
    @staticmethod
    def get_category_by_name(name: str) -> Optional[Category]:
        """
        Get a category by name.
        
        Args:
            name: Category's name
            
        Returns:
            The category object if found, None otherwise
        """
        try:
            return Category.objects.get(name=name)
        except Category.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_categories() -> List[Category]:
        """
        Get all categories.
        
        Returns:
            List of all categories
        """
        return Category.objects.all().order_by('name')
    
    @staticmethod
    def get_active_categories() -> List[Category]:
        """
        Get all active categories.
        
        Returns:
            List of active categories
        """
        return Category.objects.filter(is_active=True).order_by('name')
    
    @staticmethod
    def update_category(category: Category, **kwargs) -> Category:
        """
        Update a category.
        
        Args:
            category: The category to update
            **kwargs: Fields to update
            
        Returns:
            The updated category object
        """
        for key, value in kwargs.items():
            setattr(category, key, value)
        
        category.save()
        return category
    
    @staticmethod
    def delete_category(category: Category) -> None:
        """
        Delete a category.
        
        Args:
            category: The category to delete
        """
        category.delete()
    
    @staticmethod
    def activate_category(category: Category) -> Category:
        """
        Activate a category.
        
        Args:
            category: The category to activate
            
        Returns:
            The activated category object
        """
        category.is_active = True
        category.save()
        return category
    
    @staticmethod
    def deactivate_category(category: Category) -> Category:
        """
        Deactivate a category.
        
        Args:
            category: The category to deactivate
            
        Returns:
            The deactivated category object
        """
        category.is_active = False
        category.save()
        return category
