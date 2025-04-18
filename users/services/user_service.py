from users.repositories.user_repository import UserRepository
from users.models import CustomUser
from typing import List, Dict, Any, Optional


class UserService:
    """
    Service class for user-related operations.
    This class handles business logic related to users.
    """
    
    @staticmethod
    def register_user(email: str, name: str, password: str, **extra_fields) -> CustomUser:
        """
        Register a new user.
        
        Args:
            email: User's email address
            name: User's full name
            password: User's password
            **extra_fields: Additional fields for the user
            
        Returns:
            The created user object
            
        Raises:
            ValueError: If email or name is empty
        """
        if not email:
            raise ValueError("Email is required")
        if not name:
            raise ValueError("Name is required")
        if not password:
            raise ValueError("Password is required")
            
        # Check if user with this email already exists
        existing_user = UserRepository.get_user_by_email(email)
        if existing_user:
            raise ValueError(f"User with email {email} already exists")
            
        return UserRepository.create_user(
            email=email,
            name=name,
            password=password,
            **extra_fields
        )
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[CustomUser]:
        """
        Get a user by email.
        
        Args:
            email: User's email address
            
        Returns:
            The user object if found, None otherwise
        """
        return UserRepository.get_user_by_email(email)
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[CustomUser]:
        """
        Get a user by ID.
        
        Args:
            user_id: User's ID
            
        Returns:
            The user object if found, None otherwise
        """
        return UserRepository.get_user_by_id(user_id)
    
    @staticmethod
    def search_users(query: str) -> List[CustomUser]:
        """
        Search for users by name or email.
        
        Args:
            query: Search query
            
        Returns:
            List of matching users
        """
        return UserRepository.search_users(query)
    
    @staticmethod
    def update_user(user: CustomUser, **kwargs) -> CustomUser:
        """
        Update a user's information.
        
        Args:
            user: The user to update
            **kwargs: Fields to update
            
        Returns:
            The updated user object
        """
        # Special handling for password
        if 'password' in kwargs:
            user.set_password(kwargs.pop('password'))
            user.save()
            
        return UserRepository.update_user(user, **kwargs)
    
    @staticmethod
    def delete_user(user: CustomUser) -> None:
        """
        Delete a user.
        
        Args:
            user: The user to delete
        """
        UserRepository.delete_user(user)
    
    @staticmethod
    def change_password(user: CustomUser, old_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user: The user whose password to change
            old_password: The user's current password
            new_password: The new password
            
        Returns:
            True if password was changed successfully, False otherwise
            
        Raises:
            ValueError: If the old password is incorrect
        """
        if not user.check_password(old_password):
            raise ValueError("Current password is incorrect")
            
        user.set_password(new_password)
        user.save()
        return True
