from typing import Any, Dict, List, Optional
from decimal import Decimal
from django.db.models import Q, Avg, Sum, Count, Max, Min
from django.utils import timezone
from django.core.exceptions import ValidationError
from base.services.logging import LoggingService
from base.utils.responses import RepositoryResponse
from .repository import BidRepository
from .models import Bid, BidHistory
from ads.models import Ad
from users.models import User
from .serializer import BidListSerializer, BidStatsSerializer

logging_service = LoggingService()


class BidService:
    def __init__(self, bid_repository: BidRepository):
        self.repository = bid_repository

    def create_bid(
        self, 
        ad_id: int, 
        bid_price_per_unit: float, 
        volume_requested: float,
        user: Optional[User] = None, 
        volume_type: str = "partial",
        notes: str = "",
        max_auto_bid_price: Optional[float] = None
    ) -> Bid:
        """Create a new bid with comprehensive validation"""
        try:
            # Get the ad
            ad = Ad.objects.get(id=ad_id, is_active=True)
            
            # Validate user can bid
            if not user or not user.is_authenticated:
                raise ValueError("Authentication required")
            
            if user == ad.user:
                raise ValueError("You cannot bid on your own ad")
            
            # Check auction timing
            if ad.auction_end_date and ad.auction_end_date < timezone.now():
                raise ValueError("Auction has ended")
            
            # Validate bid price
            if ad.starting_bid_price and Decimal(str(bid_price_per_unit)) < ad.starting_bid_price:
                raise ValueError(f"Bid must be at least {ad.starting_bid_price} {ad.currency}")
            
            # Check against current highest bid
            current_highest = self.get_highest_bid_for_ad(ad_id)
            if current_highest and Decimal(str(bid_price_per_unit)) <= current_highest.bid_price_per_unit:
                raise ValueError(f"Bid must be higher than current highest bid of {current_highest.bid_price_per_unit} {ad.currency}")
            
            # Validate volume
            if ad.minimum_order_quantity and Decimal(str(volume_requested)) < ad.minimum_order_quantity:
                raise ValueError(f"Volume must be at least {ad.minimum_order_quantity} {ad.unit_of_measurement}")
            
            if Decimal(str(volume_requested)) > ad.available_quantity:
                raise ValueError(f"Volume cannot exceed available quantity of {ad.available_quantity} {ad.unit_of_measurement}")

            data = {
                "ad_id": ad_id,
                "bid_price_per_unit": bid_price_per_unit,
                "volume_requested": volume_requested,
                "volume_type": volume_type,
                "notes": notes,
            }
            
            if max_auto_bid_price:
                data["max_auto_bid_price"] = max_auto_bid_price

            response = self.repository.place_bid(data, user)

            if not response.success:
                raise ValueError(response.message)

            bid = response.data
            
            # Update other bids status and handle auto-bidding
            self._update_bid_statuses(ad_id, bid.id)
            self._handle_auto_bidding(ad_id, bid)
            
            # Create history entry
            BidHistory.objects.create(
                bid=bid,
                new_price=bid.bid_price_per_unit,
                new_volume=bid.volume_requested,
                change_reason='bid_placed'
            )

            return bid

        except Ad.DoesNotExist:
            raise ValueError("Ad not found or inactive")
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def update_bid(self, bid_id: int, bid_price_per_unit: Optional[float] = None, 
                   volume_requested: Optional[float] = None, user: Optional[User] = None, 
                   notes: Optional[str] = None) -> dict:
        """Update an existing bid"""
        try:
            if not user or not user.is_authenticated:
                return {"error": "Authentication required"}

            bid = Bid.objects.select_related('ad').get(id=bid_id, user=user)
            
            # Check if auction is still active
            if bid.ad.auction_end_date and bid.ad.auction_end_date < timezone.now():
                return {"error": "Cannot update bid - auction has ended"}
            
            # Store previous values
            previous_price = bid.bid_price_per_unit
            previous_volume = bid.volume_requested
            
            # Update fields
            if bid_price_per_unit is not None:
                # Validate new price
                new_price = Decimal(str(bid_price_per_unit))
                if bid.ad.starting_bid_price and new_price < bid.ad.starting_bid_price:
                    return {"error": f"Bid must be at least {bid.ad.starting_bid_price} {bid.ad.currency}"}
                
                # Check against other bids
                highest_other_bid = Bid.objects.filter(
                    ad=bid.ad,
                    status__in=['active', 'winning']
                ).exclude(id=bid.id).order_by('-bid_price_per_unit').first()
                
                if highest_other_bid and new_price <= highest_other_bid.bid_price_per_unit:
                    return {"error": f"Bid must be higher than current highest bid of {highest_other_bid.bid_price_per_unit} {bid.ad.currency}"}
                
                bid.bid_price_per_unit = new_price
            
            if volume_requested is not None:
                new_volume = Decimal(str(volume_requested))
                if bid.ad.minimum_order_quantity and new_volume < bid.ad.minimum_order_quantity:
                    return {"error": f"Volume must be at least {bid.ad.minimum_order_quantity} {bid.ad.unit_of_measurement}"}
                
                if new_volume > bid.ad.available_quantity:
                    return {"error": f"Volume cannot exceed available quantity of {bid.ad.available_quantity} {bid.ad.unit_of_measurement}"}
                
                bid.volume_requested = new_volume
            
            if notes is not None:
                bid.notes = notes
            
            bid.save()
            
            # Create history entry
            BidHistory.objects.create(
                bid=bid,
                previous_price=previous_price,
                new_price=bid.bid_price_per_unit,
                previous_volume=previous_volume,
                new_volume=bid.volume_requested,
                change_reason='bid_updated'
            )
            
            # Update bid statuses
            self._update_bid_statuses(bid.ad.id, bid.id)

            return {
                "message": "Bid updated successfully",
                "bid": bid
            }

        except Bid.DoesNotExist:
            return {"error": "Bid not found or you don't have permission to update it"}
        except Exception as e:
            logging_service.log_error(e)
            return {"error": "Something went wrong"}

    def delete_bid(self, bid_id: int, user: Optional[User] = None) -> None:
        """Delete a bid (mark as cancelled)"""
        try:
            bid = Bid.objects.get(id=bid_id, user=user)
            
            # Check if auction is still active
            if bid.ad.auction_end_date and bid.ad.auction_end_date < timezone.now():
                raise ValueError("Cannot delete bid - auction has ended")
            
            bid.status = 'cancelled'
            bid.save()
            
            # Update other bid statuses
            self._update_bid_statuses(bid.ad.id)
            
        except Bid.DoesNotExist:
            raise ValueError("Bid not found or you don't have permission to delete it")
        except Exception as e:
            logging_service.log_error(e)
            raise e

    def get_bid_by_id(self, bid_id: int) -> Optional[Bid]:
        """Get a specific bid by ID"""
        try:
            return Bid.objects.select_related('user', 'ad').get(id=bid_id)
        except Bid.DoesNotExist:
            return None
        except Exception as e:
            logging_service.log_error(e)
            return None

    def get_bids_for_ad(self, ad_id: int, status_filter: Optional[str] = None) -> List[Bid]:
        """Get all bids for a specific ad"""
        try:
            queryset = Bid.objects.filter(ad_id=ad_id).select_related('user').order_by('-bid_price_per_unit', '-created_at')
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            return list(queryset)
        except Exception as e:
            logging_service.log_error(e)
            return []

    def get_user_bids(self, user: User, status_filter: Optional[str] = None) -> List[Bid]:
        """Get all bids for a specific user"""
        try:
            queryset = Bid.objects.filter(user=user).select_related('ad').order_by('-created_at')
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            return list(queryset)
        except Exception as e:
            logging_service.log_error(e)
            return []

    def get_highest_bid_for_ad(self, ad_id: int) -> Optional[Bid]:
        """Get the highest bid for an ad"""
        try:
            return Bid.objects.filter(
                ad_id=ad_id,
                status__in=['active', 'winning']
            ).order_by('-bid_price_per_unit').first()
        except Exception as e:
            logging_service.log_error(e)
            return None

    def get_bid_statistics(self, ad_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for bids on an ad"""
        try:
            bids = Bid.objects.filter(ad_id=ad_id, status__in=['active', 'winning', 'outbid'])
            
            if not bids.exists():
                return {
                    "total_bids": 0,
                    "highest_bid": None,
                    "lowest_bid": None,
                    "average_bid": None,
                    "total_volume_requested": 0,
                    "unique_bidders": 0
                }
            
            stats = bids.aggregate(
                total_bids=Count('id'),
                highest_bid=Max('bid_price_per_unit'),
                lowest_bid=Min('bid_price_per_unit'),
                average_bid=Avg('bid_price_per_unit'),
                total_volume_requested=Sum('volume_requested'),
                unique_bidders=Count('user', distinct=True)
            )
            
            return stats
            
        except Exception as e:
            logging_service.log_error(e)
            return {}

    def _update_bid_statuses(self, ad_id: int, exclude_bid_id: Optional[int] = None):
        """Update bid statuses after a new bid or bid update"""
        try:
            # Get all active bids for the ad
            bids_query = Bid.objects.filter(
                ad_id=ad_id,
                status__in=['active', 'winning']
            ).order_by('-bid_price_per_unit', '-created_at')
            
            if exclude_bid_id:
                bids_query = bids_query.exclude(id=exclude_bid_id)
            
            bids = list(bids_query)
            
            if bids:
                # Set the highest bid as winning
                highest_bid = bids[0]
                highest_bid.status = 'winning'
                highest_bid.save()
                
                # Set others as outbid
                for bid in bids[1:]:
                    if bid.status != 'outbid':
                        bid.status = 'outbid'
                        bid.save()
            
        except Exception as e:
            logging_service.log_error(e)

    def _handle_auto_bidding(self, ad_id: int, new_bid: Bid):
        """Handle auto-bidding logic when a new bid is placed"""
        try:
            # Find users with auto-bid enabled for this ad who were outbid
            auto_bid_users = Bid.objects.filter(
                ad_id=ad_id,
                status='outbid',
                max_auto_bid_price__isnull=False,
                max_auto_bid_price__gt=new_bid.bid_price_per_unit
            ).exclude(user=new_bid.user)
            
            for outbid_bid in auto_bid_users:
                # Calculate new auto-bid price (small increment above current highest)
                increment = Decimal('0.01')  # Small increment
                new_auto_price = new_bid.bid_price_per_unit + increment
                
                # Don't exceed their maximum
                if new_auto_price <= outbid_bid.max_auto_bid_price:
                    # Update their bid
                    previous_price = outbid_bid.bid_price_per_unit
                    outbid_bid.bid_price_per_unit = new_auto_price
                    outbid_bid.status = 'active'
                    outbid_bid.is_auto_bid = True
                    outbid_bid.save()
                    
                    # Create history
                    BidHistory.objects.create(
                        bid=outbid_bid,
                        previous_price=previous_price,
                        new_price=new_auto_price,
                        previous_volume=outbid_bid.volume_requested,
                        new_volume=outbid_bid.volume_requested,
                        change_reason='auto_bid'
                    )
                    
                    # Update statuses again
                    self._update_bid_statuses(ad_id, outbid_bid.id)
                    break  # Only one auto-bid per round
            
        except Exception as e:
            logging_service.log_error(e)

    def close_auction(self, ad_id: int) -> Dict[str, Any]:
        """Close auction and determine winner"""
        try:
            ad = Ad.objects.get(id=ad_id)
            winning_bid = self.get_highest_bid_for_ad(ad_id)
            
            if winning_bid:
                # Check reserve price
                if ad.reserve_price and winning_bid.bid_price_per_unit < ad.reserve_price:
                    # Reserve not met
                    Bid.objects.filter(ad_id=ad_id, status__in=['active', 'winning']).update(status='lost')
                    return {
                        "success": False,
                        "message": "Reserve price not met",
                        "reserve_price": ad.reserve_price,
                        "highest_bid": winning_bid.bid_price_per_unit
                    }
                else:
                    # Auction successful
                    winning_bid.status = 'won'
                    winning_bid.save()
                    
                    # Mark other bids as lost
                    Bid.objects.filter(ad_id=ad_id, status__in=['active', 'outbid']).update(status='lost')
                    
                    return {
                        "success": True,
                        "message": "Auction completed successfully",
                        "winning_bid": winning_bid,
                        "final_price": winning_bid.bid_price_per_unit,
                        "volume": winning_bid.volume_requested
                    }
            else:
                return {
                    "success": False,
                    "message": "No bids received",
                    "winning_bid": None
                }
                
        except Ad.DoesNotExist:
            return {"success": False, "message": "Ad not found"}
        except Exception as e:
            logging_service.log_error(e)
            return {"success": False, "message": "Error closing auction"}
