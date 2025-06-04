from typing import Any, Dict, List, Optional
from base.services.logging import LoggingService
from base.utils.responses import RepositoryResponse
from .repository import AdRepository
from .models import Ad
from users.models import User

logging_service = LoggingService()


class AdService:
    def __init__(self, ad_repository: AdRepository):
        self.repository = ad_repository

    def create_ad(self, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> Ad:
        try:
            response = self.repository.create_ad(data, files, user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_ad(self, ad_id: int, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None, user: Optional[User] = None) -> Ad:
        try:
            response = self.repository.update_ad(ad_id, data, files, user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_ad(self, ad_id: int, user: Optional[User] = None) -> None:
        try:
            response = self.repository.delete_ad(ad_id, user)
            if not response.success:
                raise ValueError(response.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def list_ads(self) -> List[Ad]:
        try:
            response = self.repository.list_ads()
            if not response.success:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_ad_by_id(self, ad_id: int) -> Optional[Ad]:
        try:
            ad = Ad.objects.filter(id=ad_id).first()
            return ad
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def list_user_ads(self, user: User) -> List[Ad]:
        try:
            response = self.repository.list_ads_by_user(user)
            if not response.success:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_step(self, step: int, ad_id: int, data: Dict[str, Any], user: Optional[User] = None) -> Ad:
        try:
            response = self.repository.update_ad_step(ad_id, data, step=step)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e
