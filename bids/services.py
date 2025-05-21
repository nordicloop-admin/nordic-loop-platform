from typing import Any, Dict, List, Optional
from base.services.logging import LoggingService
from base.utils.responses import RepositoryResponse
from .repository import BidRepository
from .models import Bid
from users.models import User

logging_service = LoggingService()


class BidService:
    def __init__(self, bid_repository: BidRepository):
        self.repository = bid_repository

    def create_bid(self, ad_id: int, amount: float, user: Optional[User] = None, volume: Optional[float] = None) -> dict:
        try:
            data = {
                "ad_id": ad_id,
                "amount": amount,
            }
            if volume is not None:
                data["volume"] = volume

            response = self.repository.place_bid(data, user)

            if not response.success:
                return {"error": response.message}

            return response.data

        except Exception as e:
            logging_service.log_error(e)
            return {"error": "Something went wrong"}

    def update_bid(self, bid_id: int, amount: float, user: Optional[User] = None) -> Bid:
        try:
            response = self.repository.update_bid(bid_id, amount, user)
            if not response.success or not response.data:
                raise ValueError(response.message)
            return response.data  # now a Bid instance
        except Exception as e:
            logging_service.log_error(e)
            raise e


    def delete_bid(self, bid_id: int, user: Optional[User] = None) -> None:
        try:
            response = self.repository.delete_bid(bid_id, user)
            if not response.success:
                raise ValueError(response.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def list_bids(
        self,
        ad_id: Optional[int] = None,
        user: Optional[User] = None
    ) -> List[Dict[str, Any]]:
        try:
            response = self.repository.list_bids(ad_id, user)
            if not response.success:
                raise ValueError(response.message)
            return response.data
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_bid_by_id(self, bid_id: int) -> Optional[Bid]:
        try:
            bid = Bid.objects.filter(id=bid_id).first()
            return bid
        except Exception as e:
            logging_service.log_error(e)
            raise e
