from .models import Bid
from ads.models import Ad
from users.models import User
from base.utils.responses import RepositoryResponse
from base.services.logging import LoggingService
from django.utils import timezone
from datetime import datetime

logging_service = LoggingService()


class BidRepository:
    def place_bid(self, data, user=None) -> RepositoryResponse:
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            ad_id = data.get("ad_id")
            amount = data.get("amount")

            if not ad_id or not amount:
                return RepositoryResponse(False, "Ad ID and bid amount are required", None)

            ad = Ad.objects.filter(id=ad_id).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found", None)

            # Combine end_date and end_time into a timezone-aware datetime
            end_datetime = datetime.combine(ad.end_date, ad.end_time)
            end_datetime = timezone.make_aware(end_datetime, timezone.get_current_timezone())

            if end_datetime < timezone.now():
                return RepositoryResponse(False, "Bidding has ended for this ad", None)

            highest_bid = ad.bids.order_by("-amount").first()
            if highest_bid and float(amount) <= float(highest_bid.amount):
                return RepositoryResponse(
                    False,
                    f"Your bid must be higher than the current highest bid of {highest_bid.amount}",
                    None
                )

            bid = Bid.objects.create(user=user, ad=ad, amount=amount)

            return RepositoryResponse(
                success=True,
                message="Bid placed successfully",
                data=bid
            )

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to place bid", None)
        
    

    def update_bid(self, bid_id, new_amount, user=None) -> RepositoryResponse:
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            bid = Bid.objects.filter(id=bid_id, user=user).first()
            if not bid:
                return RepositoryResponse(False, "Bid not found or not owned by user", None)

            # Rebuild end_datetime from separate fields on the ad
            ad = bid.ad
            end_datetime = datetime.combine(ad.end_date, ad.end_time)
            end_datetime = timezone.make_aware(end_datetime, timezone.get_current_timezone())

            if end_datetime < timezone.now():
                return RepositoryResponse(False, "Bidding has ended. Cannot update bid.", None)

            highest_bid = ad.bids.exclude(id=bid.id).order_by("-amount").first()
            if highest_bid and new_amount <= highest_bid.amount:
                return RepositoryResponse(
                    False,
                    f"Your new bid must be higher than the current highest bid of {highest_bid.amount}",
                    None
                )

            bid.amount = new_amount
            bid.save()

            return RepositoryResponse(True, "Bid updated successfully", bid)
                

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to update bid", None)



    def delete_bid(self, bid_id, user=None) -> RepositoryResponse:
        try:
            if not user or not user.is_authenticated:
                return RepositoryResponse(False, "Authentication required", None)

            bid = Bid.objects.filter(id=bid_id, user=user).first()
            if not bid:
                return RepositoryResponse(False, "Bid not found or not owned by user", None)

            # Combine end_date and end_time into a datetime object
            ad_end_datetime = datetime.combine(bid.ad.end_date, bid.ad.end_time)
            ad_end_datetime = timezone.make_aware(ad_end_datetime)

            if ad_end_datetime < timezone.now():
                return RepositoryResponse(False, "Bidding has ended. Cannot delete bid.", None)

            bid.delete()
            return RepositoryResponse(True, "Bid deleted successfully", None)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to delete bid", None)
    



    def list_bids(self, ad_id=None, user=None) -> RepositoryResponse:
        try:
            bids = Bid.objects.all()

            if ad_id:
                bids = bids.filter(ad_id=ad_id)
            if user:
                bids = bids.filter(user=user)

            bids = bids.order_by("-timestamp")

            serialized = [
                {
                    "bid_id": bid.id,
                    "amount": str(bid.amount),
                    "timestamp": bid.timestamp,
                    "ad_id": bid.ad.id,
                    "user_id": bid.user.id,
                    "username": bid.user.username,
                }
                for bid in bids
            ]

            return RepositoryResponse(True, "Bids retrieved successfully", serialized)

        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, "Failed to list bids", None)
        
    



