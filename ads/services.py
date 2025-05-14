from typing import Any, Dict, List, Optional
from base.services.logging import LoggingService
from base.utils.responses import RepositoryResponse
from .repository import AdRepository
from .models import Ad

logging_service = LoggingService()


class AdService:
    def __init__(self, ad_repository: AdRepository):
        self.repository = ad_repository

    def create_ad(self, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None) -> Ad:
        try:
            response = self.repository.create_ad(data, files)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_ad(self, ad_id: int, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None) -> Ad:
        try:
            response = self.repository.update_ad(ad_id, data, files)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def delete_ad(self, ad_id: int) -> None:
        try:
            response = self.repository.delete_ad(ad_id)
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
