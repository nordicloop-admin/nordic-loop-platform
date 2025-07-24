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

    def get_admin_ads_filtered(self, search=None, status=None, page=1, page_size=10) -> Dict[str, Any]:
        """
        Get filtered ads for admin with pagination
        """
        try:
            result = self.repository.get_admin_ads_filtered(search, status, page, page_size)
            if result.success:
                return result.data
            else:
                raise Exception(result.message)
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
            if response.success:
                return response.data
            else:
                raise Exception(response.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def admin_approve_ad(self, ad_id: int, admin_user: User) -> Ad:
        """Admin approval for an ad"""
        try:
            response = self.repository.admin_approve_ad(ad_id, admin_user)
            if response.success:
                return response.data
            else:
                raise Exception(response.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def admin_suspend_ad(self, ad_id: int, admin_user: User) -> Ad:
        """Admin suspension for an ad"""
        try:
            response = self.repository.admin_suspend_ad(ad_id, admin_user)
            if response.success:
                return response.data
            else:
                raise Exception(response.message)
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

    def get_admin_addresses_filtered(self, search=None, type_filter=None, is_verified=None, page=1, page_size=10) -> Dict[str, Any]:
        """
        Get filtered addresses for admin with pagination
        """
        try:
            result = self.repository.get_admin_addresses_filtered(search, type_filter, is_verified, page, page_size)
            if result.success:
                return result.data
            else:
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_address_by_id(self, address_id: int):
        """
        Get address by ID for admin
        """
        try:
            result = self.repository.get_address_by_id(address_id)
            if result.success:
                return result.data
            else:
                if "not found" in result.message.lower():
                    return None
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_address_verification(self, address_id: int, is_verified: bool):
        """
        Update address verification status for admin
        """
        try:
            result = self.repository.update_address_verification(address_id, is_verified)
            if result.success:
                return result.data
            else:
                if "not found" in result.message.lower():
                    return None
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_admin_subscriptions_filtered(self, search=None, plan=None, status=None, page=1, page_size=10) -> Dict[str, Any]:
        """
        Get filtered subscriptions for admin with pagination
        """
        try:
            result = self.repository.get_admin_subscriptions_filtered(search, plan, status, page, page_size)
            if result.success:
                return result.data
            else:
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_subscription_by_id(self, subscription_id: int):
        """
        Get subscription by ID for admin
        """
        try:
            result = self.repository.get_subscription_by_id(subscription_id)
            if result.success:
                return result.data
            else:
                if "not found" in result.message.lower():
                    return None
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_company_subscription(self, company_id: int):
        """
        Get the latest subscription for a company
        """
        try:
            result = self.repository.get_company_subscription(company_id)
            if result.success:
                return result.data
            return None
        except Exception as e:
            logging_service.log_error(e)
            return None
            
    def create_subscription(self, company_id: int, subscription_data: dict):
        """
        Create a new subscription for a company
        Returns a tuple of (subscription, error_message)
        If successful, subscription will be the Subscription object and error_message will be None
        If failed, subscription will be None and error_message will contain the error
        """
        try:
            result = self.repository.create_subscription(company_id, subscription_data)
            if result.success:
                return result.data, None
            return None, result.message
        except Exception as e:
            logging_service.log_error(e)
            return None, str(e)
            
    def get_company_addresses(self, company_id: int) -> List:
        """
        Get all addresses for a company
        """
        try:
            result = self.repository.get_company_addresses(company_id)
            if result.success:
                return result.data
            return []
        except Exception as e:
            logging_service.log_error(e)
            return []
            
    def create_company_address(self, company_id: int, address_data: dict):
        """
        Create a new address for a company
        """
        try:
            result = self.repository.create_company_address(company_id, address_data)
            if result.success:
                return result.data
            return None
        except Exception as e:
            logging_service.log_error(e)
            return None
            
    def get_address_by_id_for_company(self, address_id: int, company_id: int):
        """
        Get a specific address by ID, ensuring it belongs to the specified company
        """
        try:
            result = self.repository.get_address_by_id_for_company(address_id, company_id)
            if result.success:
                return result.data
            return None
        except Exception as e:
            logging_service.log_error(e)
            return None
            
    def update_company_address(self, address_id: int, company_id: int, address_data: dict):
        """Update an existing address for a company"""
        try:
            result = self.repository.update_company_address(address_id, company_id, address_data)
            if not result.success:
                return None
            return result.data
        except Exception as e:
            logging_service.log_error(e)
            return None
            
    def delete_company_address(self, address_id: int, company_id: int):
        """Delete an address for a company"""
        try:
            result = self.repository.delete_company_address(address_id, company_id)
            return result.success
        except Exception as e:
            logging_service.log_error(e)
            return False
