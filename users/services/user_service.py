from users.repositories.user_repository import UserRepository
from base.services.logging import LoggingService
from users.models import CustomUser
from typing import List, Optional

logging_service = LoggingService()


class UserService:
    """
    Service class for user-related operations.
    This class handles business logic related to users.
    """

    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository

    def register_user(self, email: str, name: str, password: str, **extra_fields) -> CustomUser:
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
        try:
            if not email:
                raise ValueError("Email is required")
            if not name:
                raise ValueError("Name is required")
            if not password:
                raise ValueError("Password is required")

            # Check if user with this email already exists
            existing_user = self.repository.get_user_by_email(email).data
            if existing_user:
                raise ValueError(f"User with email {email} already exists")

            user = self.repository.create_user(
                email=email,
                name=name,
                password=password,
                **extra_fields
            ).data
            return user
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_user_by_email(self, email: str) -> Optional[CustomUser]:
        """
        Get a user by email.

        Args:
            email: User's email address

        Returns:
            The user object if found, None otherwise
        """
        try:
            user = self.repository.get_user_by_email(email).data
            return user
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_user_by_id(self, user_id: int) -> Optional[CustomUser]:
        """
        Get a user by ID.

        Args:
            user_id: User's ID

        Returns:
            The user object if found, None otherwise
        """
        try:
            user = self.repository.get_user_by_id(user_id).data
            return user
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def search_users(self, query: str) -> List[CustomUser]:
        """
        Search for users by name or email.

        Args:
            query: Search query

        Returns:
            List of matching users
        """
        try:
            users = self.repository.search_users(query).data
            return users
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_user(self, user: CustomUser, **kwargs) -> CustomUser:
        """
        Update a user's information.

        Args:
            user: The user to update
            **kwargs: Fields to update

        Returns:
            The updated user object
        """
        try:
            # Special handling for password
            if 'password' in kwargs:
                user.set_password(kwargs.pop('password'))
                user.save()

            updated_user = self.repository.update_user(user.id, kwargs).data
            return updated_user
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_user(self, user: CustomUser) -> None:
        """
        Delete a user.

        Args:
            user: The user to delete
        """
        try:
            self.repository.delete_user(user.id)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def change_password(self, user: CustomUser, old_password: str, new_password: str) -> bool:
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
        try:
            if not user.check_password(old_password):
                raise ValueError("Current password is incorrect")

            user.set_password(new_password)
            user.save()
            return True
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def create_company_user(self, email: str, name: str, password: str, is_active: bool = False) -> CustomUser:
        """
        Create a user associated with a company registration.

        Args:
            email: User's email address
            name: User's full name
            password: User's password
            is_active: Whether the user should be active (default: False)

        Returns:
            The created user object
        """
        try:
            user = self.register_user(
                email=email,
                name=name,
                password=password,
                is_active=is_active
            )
            return user
        except Exception as e:
            logging_service.log_error(e)
            raise e
