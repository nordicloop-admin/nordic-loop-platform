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
            # Validate user authentication
            if not user or not user.is_authenticated:
                raise ValueError("User authentication required")

            # Validate ad exists and is active
            try:
                ad = Ad.objects.get(id=ad_id)
            except Ad.DoesNotExist:
                raise ValueError("Ad not found")

            if not ad.is_active or not ad.is_complete:
                raise ValueError("Cannot bid on inactive or incomplete ads")

            # Check if user is not the ad owner
            if user == ad.user:
                raise ValueError("You cannot bid on your own ad")

            # Validate bid constraints
            if bid_price_per_unit <= 0:
                raise ValueError("Bid price must be greater than zero")

            if volume_requested <= 0:
                raise ValueError("Volume requested must be greater than zero")

            # Check ad constraints
            if ad.starting_bid_price and bid_price_per_unit < float(ad.starting_bid_price):
                raise ValueError(f"Bid price must be at least {ad.starting_bid_price}")

            if ad.minimum_order_quantity and volume_requested < float(ad.minimum_order_quantity):
                raise ValueError(f"Volume must be at least {ad.minimum_order_quantity}")

            if volume_requested > float(ad.available_quantity):
                raise ValueError(f"Volume cannot exceed {ad.available_quantity}")

            # Prepare bid data
            data = {
                'ad_id': ad_id,
                'bid_price_per_unit': bid_price_per_unit,
                'volume_requested': volume_requested,
                'volume_type': volume_type,
                'notes': notes,
            }

            if max_auto_bid_price:
                data['max_auto_bid_price'] = max_auto_bid_price

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

    def update_bid(
        self, 
        bid_id: int,
        bid_price_per_unit: Optional[float] = None,
        volume_requested: Optional[float] = None,
        notes: Optional[str] = None,
        user: Optional[User] = None
    ) -> Bid:
        """Update an existing bid"""
        try:
            if not user or not user.is_authenticated:
                raise ValueError("User authentication required")

            bid = Bid.objects.get(id=bid_id, user=user)
            
            # Check if bid can be updated
            if bid.status in ['won', 'lost', 'cancelled']:
                raise ValueError("Cannot update bid with status: " + bid.status)

            # Validate new constraints if provided
            data = {}
            if bid_price_per_unit is not None:
                if bid_price_per_unit <= 0:
                    raise ValueError("Bid price must be greater than zero")
                if bid.ad.starting_bid_price and bid_price_per_unit < float(bid.ad.starting_bid_price):
                    raise ValueError(f"Bid price must be at least {bid.ad.starting_bid_price}")
                data['bid_price_per_unit'] = bid_price_per_unit

            if volume_requested is not None:
                if volume_requested <= 0:
                    raise ValueError("Volume requested must be greater than zero")
                if bid.ad.minimum_order_quantity and volume_requested < float(bid.ad.minimum_order_quantity):
                    raise ValueError(f"Volume must be at least {bid.ad.minimum_order_quantity}")
                if volume_requested > float(bid.ad.available_quantity):
                    raise ValueError(f"Volume cannot exceed {bid.ad.available_quantity}")
                data['volume_requested'] = volume_requested

            if notes is not None:
                data['notes'] = notes

            response = self.repository.update_existing_bid(bid, data)
            if not response.success:
                raise ValueError(response.message)

            updated_bid = response.data
            
            # Update bid statuses for the ad
            self._update_bid_statuses(bid.ad.id)
            
            return updated_bid

        except Bid.DoesNotExist:
            raise ValueError("Bid not found or you don't have permission to update it")
        except Exception as e:
            logging_service.log_error(e)
            raise e

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

    def get_admin_bids_filtered(self, search=None, status=None, page=1, page_size=10) -> Dict[str, Any]:
        """
        Get filtered bids for admin with pagination
        """
        try:
            result = self.repository.get_admin_bids_filtered(search, status, page, page_size)
            if result.success:
                return result.data
            else:
                raise Exception(result.message)
        except Exception as e:
            logging_service.log_error(e)
            raise e

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
        """Handle automatic bidding for users who were outbid"""
        try:
            # Get users with auto-bidding enabled who were outbid
            outbid_users = self.repository.get_outbid_users_for_auto_bidding(
                ad_id, new_bid.bid_price_per_unit
            )
            
            for outbid_bid in outbid_users:
                # Calculate new auto bid price (increment by minimum step)
                increment = Decimal('0.01')  # You can make this configurable
                new_auto_price = new_bid.bid_price_per_unit + increment
                
                # Check if within auto bid limit
                if new_auto_price <= outbid_bid.max_auto_bid_price:
                    # Place auto bid
                    auto_bid_data = {
                        'bid_price_per_unit': float(new_auto_price),
                        'volume_requested': float(outbid_bid.volume_requested),
                        'volume_type': outbid_bid.volume_type,
                        'notes': outbid_bid.notes + " (Auto-bid)"
                    }
                    
                    # Update the existing bid instead of creating new one
                    auto_response = self.repository.update_existing_bid(outbid_bid, auto_bid_data)
                    if auto_response.success:
                        # Mark as auto bid
                        auto_bid = auto_response.data
                        auto_bid.is_auto_bid = True
                        auto_bid.save()
                        
                        # Create history entry
                        BidHistory.objects.create(
                            bid=auto_bid,
                            previous_price=outbid_bid.bid_price_per_unit,
                            new_price=auto_bid.bid_price_per_unit,
                            previous_volume=outbid_bid.volume_requested,
                            new_volume=auto_bid.volume_requested,
                            change_reason='auto_bid'
                        )
            
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
            
    def admin_approve_bid(self, bid_id: int, admin_user: User) -> dict:
        """
        Admin approval for a bid
        """
        try:
            response = self.repository.admin_approve_bid(bid_id, admin_user)
            if not response.success:
                raise ValueError(response.message)
            
            return {
                "success": True,
                "message": "Bid approved successfully",
                "data": response.data
            }
            
        except Exception as e:
            logging_service.log_error(e)
            return {
                "success": False,
                "message": f"Failed to approve bid: {str(e)}"
            }
    
    def admin_reject_bid(self, bid_id: int, admin_user: User) -> dict:
        """
        Admin rejection for a bid
        """
        try:
            response = self.repository.admin_reject_bid(bid_id, admin_user)
            if not response.success:
                raise ValueError(response.message)
            
            return {
                "success": True,
                "message": "Bid rejected successfully",
                "data": response.data
            }
            
        except Exception as e:
            logging_service.log_error(e)
            return {
                "success": False,
                "message": f"Failed to reject bid: {str(e)}"
            }
    
    def admin_mark_bid_as_won(self, bid_id: int, admin_user: User) -> dict:
        """
        Admin marks a bid as won
        """
        try:
            response = self.repository.admin_mark_bid_as_won(bid_id, admin_user)
            if not response.success:
                raise ValueError(response.message)
            
            return {
                "success": True,
                "message": "Bid marked as won successfully",
                "data": response.data
            }
            
        except Exception as e:
            logging_service.log_error(e)
            return {
                "success": False,
                "message": f"Failed to mark bid as won: {str(e)}"
            }
