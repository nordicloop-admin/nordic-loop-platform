from users.models import User
from base.services.logging import LoggingService
from typing import Dict, Any, Optional, List
from users.repository.user_repository import UserRepository

logging_service = LoggingService()


class UserService:

    def __init__(self, user_repository: UserRepository):
        self.repository = user_repository

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get a user by ID"""
        try:
            result = self.repository.get_user_by_id(user_id)
            return result.data if result.success else None
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_admin_users_filtered(self, search=None, company=None, is_active=None, page=1, page_size=10) -> Dict[str, Any]:
        """
        Get filtered users for admin with pagination
        """
        try:
            result = self.repository.get_admin_users_filtered(search, company, is_active, page, page_size)
            if result.success:
                return result.data
            else:
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def list_users(self) -> List[User]:
        """List all users"""
        try:
            result = self.repository.list_users()
            return result.data if result.success else []
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        try:
            result = self.repository.create_user(user_data)
            if result.success:
                return result.data
            else:
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_user(self, user_id: int, data: Dict[str, Any]) -> User:
        """Update a user"""
        try:
            result = self.repository.update_user(user_id, data)
            if result.success:
                return result.data
            else:
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_user(self, user_id: int) -> None:
        """Delete a user"""
        try:
            result = self.repository.delete_user(user_id)
            if not result.success:
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e 