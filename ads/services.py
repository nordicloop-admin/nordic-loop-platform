from typing import Any, Dict, List, Optional
from base.services.logging import LoggingService
from base.utils.responses import RepositoryResponse
from .repository import AdRepository
from .models import Ad
from users.models import User
from django.db.models import Q

logging_service = LoggingService()


class AdService:
    def __init__(self, ad_repository: AdRepository):
        self.repository = ad_repository

    def create_new_ad(self, user: User) -> Ad:
        """Create a new empty ad for step-by-step completion"""
        try:
            response = self.repository.create_new_ad(user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def create_ad_with_step1(self, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> Ad:
        """Create a new ad with step 1 (material type) data"""
        try:
            response = self.repository.create_ad_with_step1(data, files, user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_ad_by_id(self, ad_id: int, user: Optional[User] = None) -> Optional[Ad]:
        """Get ad by ID with optional user ownership check"""
        try:
            response = self.repository.get_ad_by_id(ad_id, user)
            if not response.success:
                if "not found" in response.message.lower():
                    return None
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_ad_step(self, ad_id: int, step: int, data: Dict[str, Any], 
                      files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> Ad:
        """Update a specific step of the ad"""
        try:
            response = self.repository.update_ad_step(ad_id, step, data, files, user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_ad(self, ad_id: int, user: User) -> None:
        """Delete an ad (only by owner)"""
        try:
            response = self.repository.delete_ad(ad_id, user)
            if not response.success:
                raise ValueError(response.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def list_ads(self, category_id: Optional[int] = None, subcategory_id: Optional[int] = None,
                origin: Optional[str] = None, contamination: Optional[str] = None,
                location_country: Optional[str] = None, location_city: Optional[str] = None,
                only_complete: bool = True) -> List[Ad]:
        """List ads with optional filtering"""
        try:
            response = self.repository.list_ads(
                category_id=category_id,
                subcategory_id=subcategory_id,
                origin=origin,
                contamination=contamination,
                location_country=location_country,
                location_city=location_city,
                only_complete=only_complete
            )
            if not response.success:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def list_user_ads(self, user: User, only_complete: bool = False) -> List[Ad]:
        """List ads belonging to a specific user"""
        try:
            response = self.repository.list_user_ads(user, only_complete)
            if not response.success:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_ad_step_data(self, ad_id: int, step: int, user: Optional[User] = None) -> Dict[str, Any]:
        """Get specific step data for an ad"""
        try:
            response = self.repository.get_ad_step_data(ad_id, step, user)
            if not response.success:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def validate_step_data(self, step: int, data: Dict[str, Any]) -> bool:
        """Validate step data without saving"""
        try:
            response = self.repository.validate_step_data(step, data)
            if not response.success:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_user_ad_statistics(self, user: User) -> Dict[str, Any]:
        """Get statistics about user's ads"""
        try:
            response = self.repository.get_user_ad_statistics(user)
            if not response.success:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def activate_ad(self, ad_id: int, user: User) -> Ad:
        """Activate an ad for bidding (only if complete)"""
        try:
            response = self.repository.activate_ad(ad_id, user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def deactivate_ad(self, ad_id: int, user: User) -> Ad:
        """Deactivate an ad"""
        try:
            response = self.repository.deactivate_ad(ad_id, user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_complete_ad(self, ad_id: int, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> Ad:
        """Update complete ad with all provided fields"""
        try:
            response = self.repository.update_complete_ad(ad_id, data, files, user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def partial_update_ad(self, ad_id: int, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> Ad:
        """Partially update ad with only provided fields"""
        try:
            response = self.repository.partial_update_ad(ad_id, data, files, user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    # Legacy methods for backward compatibility (can be removed later)
    def create_ad(self, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> Ad:
        """Legacy method - use create_new_ad instead"""
        return self.create_new_ad(user)

    def update_ad(self, ad_id: int, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> Ad:
        """Legacy method - use update_ad_step instead"""
        return self.update_ad_step(ad_id, 1, data, files, user)

    def update_step(self, step: int, ad_id: int, data: Dict[str, Any], user: Optional[User] = None) -> Ad:
        """Legacy method - use update_ad_step instead"""
        return self.update_ad_step(ad_id, step, data, None, user)
