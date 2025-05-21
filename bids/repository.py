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
            volume = data.get("volume") 

            if not ad_id or not amount:
                return RepositoryResponse(False, "Ad ID and bid amount are required", None)

            ad = Ad.objects.filter(id=ad_id).first()
            if not ad:
                return RepositoryResponse(False, "Ad not found", None)

            end_datetime = datetime.combine(ad.end_date, ad.end_time)
            end_datetime = timezone.make_aware(end_datetime, timezone.get_current_timezone())
            if end_datetime < timezone.now():
                return RepositoryResponse(False, "Bidding has ended for this ad", None)

            try:
                amount = float(amount)
            except (TypeError, ValueError):
                return RepositoryResponse(False, "Invalid bid amount", None)

            if ad.selling_type == "whole":
                if volume is not None:
                    return RepositoryResponse(False, "Volume should not be specified for whole selling type", None)

                if amount < float(ad.base_price):
                    return RepositoryResponse(
                        False,
                        f"Your bid must be at least the base price of {ad.base_price}",
                        None
                    )
                bid_volume = None 

            elif ad.selling_type == "partition":
                if volume is None:
                    return RepositoryResponse(False, "Volume is required for partition bidding", None)

                try:
                    volume = float(volume)
                except (TypeError, ValueError):
                    return RepositoryResponse(False, "Volume must be a number", None)

                if volume <= 0 or volume > float(ad.volume):
                    return RepositoryResponse(
                        False,
                        f"Volume must be greater than 0 and less than or equal to available volume ({ad.volume})",
                        None
                    )

                expected_amount = float(ad.price_per_partition) * volume
                if amount < expected_amount:
                    return RepositoryResponse(
                        False,
                        f"Your bid must be at least {expected_amount} (price per partition × volume)",
                        None
                    )
                bid_volume = volume

            elif ad.selling_type == "both":
                if volume is None:
                    if amount < float(ad.base_price):
                        return RepositoryResponse(
                            False,
                            f"Your bid must be at least the base price of {ad.base_price}",
                            None
                        )
                    bid_volume = None
                else:
                    try:
                        volume = float(volume)
                    except (TypeError, ValueError):
                        return RepositoryResponse(False, "Volume must be a number", None)

                    if volume <= 0 or volume > float(ad.volume):
                        return RepositoryResponse(
                            False,
                            f"Volume must be greater than 0 and less than or equal to available volume ({ad.volume})",
                            None
                        )

                    expected_amount = float(ad.price_per_partition) * volume
                    if amount < expected_amount:
                        return RepositoryResponse(
                            False,
                            f"Your bid must be at least {expected_amount} (price per partition × volume)",
                            None
                        )
                    bid_volume = volume
            else:
                return RepositoryResponse(
                    False,
                    f"Bidding for selling type '{ad.selling_type}' is not supported",
                    None
                )

            highest_bid = ad.bids.order_by("-amount").first()
            if highest_bid and amount <= float(highest_bid.amount):
                return RepositoryResponse(
                    False,
                    f"Your bid must be higher than the current highest bid of {highest_bid.amount}",
                    None
                )
            bid = Bid.objects.create(
                user=user,
                ad=ad,
                amount=amount,
                volume=bid_volume
            )

            return RepositoryResponse(True, "Bid placed successfully", bid)

        except Exception as e:
            return RepositoryResponse(False, str(e), None)
        
    

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
        
    



