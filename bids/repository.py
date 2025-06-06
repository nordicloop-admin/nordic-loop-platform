from typing import List, Optional
from django.db.models import Q, Max, Min, Avg, Sum, Count
from django.core.exceptions import ValidationError
from decimal import Decimal

from base.utils.responses import RepositoryResponse
from .models import Bid, BidHistory
from ads.models import Ad
from users.models import User
from base.services.logging import LoggingService
from django.utils import timezone
from datetime import datetime
from decimal import Decimal, InvalidOperation

logging_service = LoggingService()


class BidRepository:
    """Repository for bid data access operations"""

    def place_bid(self, data: dict, user: User) -> RepositoryResponse:
        """Create a new bid"""
        try:
            # Check if user already has a bid for this ad
            existing_bid = Bid.objects.filter(
                user=user,
                ad_id=data['ad_id']
            ).first()
            
            if existing_bid:
                # Update existing bid instead of creating new one
                return self.update_existing_bid(existing_bid, data)
            
            # Create new bid
            bid = Bid.objects.create(
                user=user,
                ad_id=data['ad_id'],
                bid_price_per_unit=Decimal(str(data['bid_price_per_unit'])),
                volume_requested=Decimal(str(data['volume_requested'])),
                volume_type=data.get('volume_type', 'partial'),
                notes=data.get('notes', ''),
                max_auto_bid_price=Decimal(str(data['max_auto_bid_price'])) if data.get('max_auto_bid_price') else None
            )
            
            return RepositoryResponse(success=True, data=bid, message="Bid placed successfully")
            
        except ValidationError as e:
            return RepositoryResponse(success=False, message=str(e), data=None)
        except Exception as e:
            return RepositoryResponse(success=False, message=f"Error creating bid: {str(e)}", data=None)

    def update_existing_bid(self, bid: Bid, data: dict) -> RepositoryResponse:
        """Update an existing bid with new data"""
        try:
            # Store previous values for history
            previous_price = bid.bid_price_per_unit
            previous_volume = bid.volume_requested
            
            # Update bid fields
            bid.bid_price_per_unit = Decimal(str(data['bid_price_per_unit']))
            bid.volume_requested = Decimal(str(data['volume_requested']))
            bid.volume_type = data.get('volume_type', bid.volume_type)
            bid.notes = data.get('notes', bid.notes)
            
            if data.get('max_auto_bid_price'):
                bid.max_auto_bid_price = Decimal(str(data['max_auto_bid_price']))
            
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
            
            return RepositoryResponse(success=True, data=bid, message="Bid updated successfully")
            
        except ValidationError as e:
            return RepositoryResponse(success=False, message=str(e), data=None)
        except Exception as e:
            return RepositoryResponse(success=False, message=f"Error updating bid: {str(e)}", data=None)

    def update_bid(self, bid_id: int, bid_price_per_unit: float, user: User) -> RepositoryResponse:
        """Legacy method - update bid price"""
        try:
            bid = Bid.objects.get(id=bid_id, user=user)
            
            previous_price = bid.bid_price_per_unit
            bid.bid_price_per_unit = Decimal(str(bid_price_per_unit))
            bid.save()
            
            # Create history entry
            BidHistory.objects.create(
                bid=bid,
                previous_price=previous_price,
                new_price=bid.bid_price_per_unit,
                previous_volume=bid.volume_requested,
                new_volume=bid.volume_requested,
                change_reason='bid_updated'
            )
            
            return RepositoryResponse(success=True, data=bid, message="Bid updated successfully")
            
        except Bid.DoesNotExist:
            return RepositoryResponse(success=False, message="Bid not found or unauthorized", data=None)
        except Exception as e:
            return RepositoryResponse(success=False, message=f"Error updating bid: {str(e)}", data=None)

    def delete_bid(self, bid_id: int, user: User) -> RepositoryResponse:
        """Delete (cancel) a bid"""
        try:
            bid = Bid.objects.get(id=bid_id, user=user)
            bid.status = 'cancelled'
            bid.save()
            
            return RepositoryResponse(success=True, data=None, message="Bid cancelled successfully")
            
        except Bid.DoesNotExist:
            return RepositoryResponse(success=False, message="Bid not found or unauthorized", data=None)
        except Exception as e:
            return RepositoryResponse(success=False, message=f"Error deleting bid: {str(e)}", data=None)

    def get_bid_by_id(self, bid_id: int) -> Optional[Bid]:
        """Get a specific bid by ID"""
        try:
            return Bid.objects.select_related('user', 'ad').get(id=bid_id)
        except Bid.DoesNotExist:
            return None

    def get_bids_for_ad(self, ad_id: int, status_filter: Optional[str] = None) -> List[Bid]:
        """Get all bids for a specific ad"""
        try:
            queryset = Bid.objects.filter(ad_id=ad_id).select_related('user', 'ad').order_by('-bid_price_per_unit', '-created_at')
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            return list(queryset)
        except Exception:
            return []

    def get_user_bids(self, user: User, status_filter: Optional[str] = None) -> List[Bid]:
        """Get all bids for a specific user"""
        try:
            queryset = Bid.objects.filter(user=user).select_related('ad').order_by('-created_at')
            
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            return list(queryset)
        except Exception:
            return []

    def get_highest_bid_for_ad(self, ad_id: int) -> Optional[Bid]:
        """Get the highest active bid for an ad"""
        try:
            return Bid.objects.filter(
                ad_id=ad_id,
                status__in=['active', 'winning']
            ).order_by('-bid_price_per_unit', '-created_at').first()
        except Exception:
            return None

    def get_winning_bids_for_user(self, user: User) -> List[Bid]:
        """Get all winning bids for a user"""
        try:
            return list(Bid.objects.filter(
                user=user,
                status__in=['winning', 'won']
            ).select_related('ad').order_by('-created_at'))
        except Exception:
            return []

    def get_bid_statistics(self, ad_id: int) -> dict:
        """Get comprehensive bid statistics for an ad"""
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
            
        except Exception:
            return {}

    def search_bids(self, filters: dict) -> List[Bid]:
        """Search bids with various filters"""
        try:
            queryset = Bid.objects.select_related('user', 'ad').order_by('-created_at')
            
            # Apply filters
            if filters.get('ad_title'):
                queryset = queryset.filter(ad__title__icontains=filters['ad_title'])
            
            if filters.get('category'):
                queryset = queryset.filter(ad__category__name__icontains=filters['category'])
            
            if filters.get('min_price'):
                try:
                    queryset = queryset.filter(bid_price_per_unit__gte=Decimal(str(filters['min_price'])))
                except (ValueError, TypeError):
                    pass
            
            if filters.get('max_price'):
                try:
                    queryset = queryset.filter(bid_price_per_unit__lte=Decimal(str(filters['max_price'])))
                except (ValueError, TypeError):
                    pass
            
            if filters.get('status'):
                queryset = queryset.filter(status=filters['status'])
            
            if filters.get('user_id'):
                try:
                    queryset = queryset.filter(user_id=int(filters['user_id']))
                except (ValueError, TypeError):
                    pass
            
            if filters.get('volume_type'):
                queryset = queryset.filter(volume_type=filters['volume_type'])
            
            if filters.get('is_auto_bid') is not None:
                queryset = queryset.filter(is_auto_bid=bool(filters['is_auto_bid']))
            
            return list(queryset)
            
        except Exception:
            return []

    def get_outbid_users_for_auto_bidding(self, ad_id: int, current_highest_price: Decimal) -> List[Bid]:
        """Get users who were outbid and have auto-bidding enabled"""
        try:
            return list(Bid.objects.filter(
                ad_id=ad_id,
                status='outbid',
                max_auto_bid_price__isnull=False,
                max_auto_bid_price__gt=current_highest_price
            ).select_related('user'))
        except Exception:
            return []

    def update_bid_statuses_for_ad(self, ad_id: int) -> bool:
        """Update bid statuses for all bids on an ad"""
        try:
            # Get all active bids for the ad
            bids = Bid.objects.filter(
                ad_id=ad_id,
                status__in=['active', 'winning']
            ).order_by('-bid_price_per_unit', '-created_at')
            
            if bids.exists():
                bids_list = list(bids)
                
                # Set the highest bid as winning
                highest_bid = bids_list[0]
                if highest_bid.status != 'winning':
                    highest_bid.status = 'winning'
                    highest_bid.save()
                
                # Set others as outbid
                for bid in bids_list[1:]:
                    if bid.status != 'outbid':
                        bid.status = 'outbid'
                        bid.save()
            
            return True
            
        except Exception:
            return False

    def close_auction_bids(self, ad_id: int, winning_bid_id: Optional[int] = None) -> bool:
        """Close all bids for an auction"""
        try:
            if winning_bid_id:
                # Mark winning bid as won
                Bid.objects.filter(id=winning_bid_id).update(status='won')
                
                # Mark all other bids as lost
                Bid.objects.filter(
                    ad_id=ad_id,
                    status__in=['active', 'winning', 'outbid']
                ).exclude(id=winning_bid_id).update(status='lost')
            else:
                # No winner - mark all as lost
                Bid.objects.filter(
                    ad_id=ad_id,
                    status__in=['active', 'winning', 'outbid']
                ).update(status='lost')
            
            return True
            
        except Exception:
            return False

    def get_bid_history(self, bid_id: int) -> List[BidHistory]:
        """Get history for a specific bid"""
        try:
            return list(BidHistory.objects.filter(bid_id=bid_id).order_by('-timestamp'))
        except Exception:
            return []

    def list_bids(self, ad_id: Optional[int] = None, user: Optional[User] = None) -> RepositoryResponse:
        """Legacy method for listing bids"""
        try:
            queryset = Bid.objects.select_related('user', 'ad')
            
            if ad_id:
                queryset = queryset.filter(ad_id=ad_id)
            
            if user:
                queryset = queryset.filter(user=user)
            
            bids = list(queryset.order_by('-created_at'))
            
            return RepositoryResponse(success=True, data=bids, message="Bids retrieved successfully")
            
        except Exception as e:
            return RepositoryResponse(success=False, message=f"Error retrieving bids: {str(e)}", data=[])
        
    



