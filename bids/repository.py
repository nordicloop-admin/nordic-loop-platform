from typing import List, Optional
from django.db.models import Q, Max, Min, Avg, Sum, Count
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
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
            
            # Update bid fields only if provided in data
            if 'bid_price_per_unit' in data:
                bid.bid_price_per_unit = Decimal(str(data['bid_price_per_unit']))
            if 'volume_requested' in data:
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

    def get_admin_bids_filtered(self, search=None, status=None, page=1, page_size=10) -> RepositoryResponse:
        """
        Get bids for admin with filtering and pagination support
        """
        try:
            queryset = Bid.objects.select_related('user', 'ad', 'user__company').all().order_by('-created_at')
            
            # Apply search filter
            if search:
                queryset = queryset.filter(
                    Q(user__first_name__icontains=search) |
                    Q(user__last_name__icontains=search) |
                    Q(user__username__icontains=search) |
                    Q(user__email__icontains=search) |
                    Q(user__company__official_name__icontains=search) |
                    Q(ad__title__icontains=search) |
                    Q(notes__icontains=search)
                )
            
            # Apply status filter
            if status and status != 'all':
                valid_statuses = ['active', 'outbid', 'winning', 'won', 'lost', 'cancelled']
                if status in valid_statuses:
                    queryset = queryset.filter(status=status)
            
            # Apply pagination
            paginator = Paginator(queryset, page_size)
            
            try:
                bids_page = paginator.page(page)
            except:
                # If page number is out of range, return first page
                bids_page = paginator.page(1)
            
            pagination_data = {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': bids_page.number,
                'page_size': page_size,
                'next': bids_page.has_next(),
                'previous': bids_page.has_previous(),
                'results': list(bids_page.object_list)
            }
            
            return RepositoryResponse(
                success=True,
                message="Bids retrieved successfully",
                data=pagination_data,
            )
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(
                success=False,
                message="Failed to get bids",
                data=None,
            )

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

    def get_user_bids_paginated(self, user: User, status: Optional[str] = None, page: int = 1, page_size: int = 10) -> RepositoryResponse:
        """Get paginated user bids with filtering"""
        try:
            # Base queryset
            queryset = Bid.objects.filter(user=user).select_related('ad').order_by('-created_at')

            # Apply status filter
            if status and status != 'all':
                valid_statuses = ['active', 'outbid', 'winning', 'won', 'lost', 'cancelled']
                if status in valid_statuses:
                    queryset = queryset.filter(status=status)

            # Apply pagination
            paginator = Paginator(queryset, page_size)

            try:
                bids_page = paginator.page(page)
            except:
                # If page number is out of range, return first page
                bids_page = paginator.page(1)

            pagination_data = {
                'count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': bids_page.number,
                'page_size': page_size,
                'next': f"?page={bids_page.next_page_number()}" if bids_page.has_next() else None,
                'previous': f"?page={bids_page.previous_page_number()}" if bids_page.has_previous() else None,
                'results': list(bids_page.object_list)
            }

            return RepositoryResponse(
                success=True,
                message="User bids retrieved successfully",
                data=pagination_data,
            )

        except Exception as e:
            return RepositoryResponse(
                success=False,
                message=f"Failed to retrieve user bids: {str(e)}",
                data=None,
            )

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
            
        except Exception as e:
            logging_service.log_error(e)
            return {}

    def search_bids(self, filters: dict) -> RepositoryResponse:
        """Search bids with filters"""
        try:
            queryset = Bid.objects.select_related('user', 'ad').all()
            
            # Apply filters here
            if 'status' in filters and filters['status']:
                queryset = queryset.filter(status=filters['status'])
                
            if 'user_id' in filters and filters['user_id']:
                queryset = queryset.filter(user_id=filters['user_id'])
                
            if 'ad_id' in filters and filters['ad_id']:
                queryset = queryset.filter(ad_id=filters['ad_id'])
            
            # Sort by most recent
            queryset = queryset.order_by('-created_at')
            
            return RepositoryResponse(
                success=True,
                data=list(queryset),
                message="Bids found"
            )
            
            if filters.get('date_to'):
                queryset = queryset.filter(created_at__lte=filters['date_to'])
            
            # Filter by keyword (search in notes or ad title)
            if filters.get('keyword'):
                keyword = filters['keyword']
                queryset = queryset.filter(
                    Q(notes__icontains=keyword) |
                    Q(ad__title__icontains=keyword) |
                    Q(user__username__icontains=keyword)
                )
            
            return list(queryset.order_by('-created_at'))
            
        except Exception as e:
            logging_service.log_error(e)
            return []

    def get_outbid_users_for_auto_bidding(self, ad_id: int, current_highest_price: Decimal) -> List[Bid]:
        """Get users with auto-bidding enabled who were outbid"""
        try:
            return list(Bid.objects.filter(
                ad_id=ad_id,
                status='outbid',
                max_auto_bid_price__gt=current_highest_price,
                max_auto_bid_price__isnull=False
            ).select_related('user').order_by('-max_auto_bid_price'))
        except Exception:
            return []

    def update_bid_statuses_for_ad(self, ad_id: int) -> bool:
        """Update all bid statuses for an ad based on current highest bid"""
        try:
            # Get all active bids for this ad
            active_bids = Bid.objects.filter(
                ad_id=ad_id,
                status__in=['active', 'winning']
            ).order_by('-bid_price_per_unit', '-created_at')
            
            if not active_bids.exists():
                return True
            
            # Set the highest bid as winning
            highest_bid = active_bids.first()
            highest_bid.status = 'winning'
            highest_bid.save()
            
            # Set all other bids as outbid
            for bid in active_bids[1:]:
                bid.status = 'outbid'
                bid.save()
            
            return True
            
        except Exception as e:
            logging_service.log_error(e)
            return False

    def close_auction_bids(self, ad_id: int, winning_bid_id: Optional[int] = None) -> bool:
        """Close auction and set final bid statuses"""
        try:
            if winning_bid_id:
                # Mark specific bid as won
                winning_bid = Bid.objects.get(id=winning_bid_id, ad_id=ad_id)
                winning_bid.status = 'won'
                winning_bid.save()
                
                # Mark all other bids as lost
                Bid.objects.filter(ad_id=ad_id).exclude(id=winning_bid_id).update(status='lost')
            else:
                # No winner - mark all bids as lost
                Bid.objects.filter(ad_id=ad_id).update(status='lost')
            
            return True
            
        except Exception as e:
            logging_service.log_error(e)
            return False

    def get_bid_history(self, bid_id: int) -> List[BidHistory]:
        """Get bid modification history"""
        try:
            return list(BidHistory.objects.filter(bid_id=bid_id).order_by('-timestamp'))
        except Exception:
            return []

    def list_bids(self, ad_id: Optional[int] = None, user: Optional[User] = None) -> RepositoryResponse:
        """List bids with optional filtering by ad or user"""
        try:
            queryset = Bid.objects.select_related('user', 'ad').all()
            
            if ad_id:
                queryset = queryset.filter(ad_id=ad_id)
            
            if user:
                queryset = queryset.filter(user=user)
            
            bids = list(queryset.order_by('-created_at'))
            
            return RepositoryResponse(success=True, data=bids, message="Bids retrieved successfully")
            
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(success=False, data=None, message="Failed to retrieve bids")
            
    def admin_approve_bid(self, bid_id: int, admin_user: User) -> RepositoryResponse:
        """
        Admin approval for a bid
        """
        try:
            # Verify the user is an admin
            if not admin_user.is_staff and not admin_user.is_superuser:
                return RepositoryResponse(False, "Only administrators can approve bids", None)
                
            # Get the bid regardless of owner
            bid = Bid.objects.filter(id=bid_id).first()
            if not bid:
                return RepositoryResponse(False, "Bid not found", None)
                
            # Update the bid status
            bid.status = "active"
            bid.save()
            
            return RepositoryResponse(True, "Bid approved by administrator", bid)
            
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, f"Failed to approve bid: {str(e)}", None)
            
    def admin_reject_bid(self, bid_id: int, admin_user: User) -> RepositoryResponse:
        """
        Admin rejection for a bid
        """
        try:
            # Verify the user is an admin
            if not admin_user.is_staff and not admin_user.is_superuser:
                return RepositoryResponse(False, "Only administrators can reject bids", None)
                
            # Get the bid regardless of owner
            bid = Bid.objects.filter(id=bid_id).first()
            if not bid:
                return RepositoryResponse(False, "Bid not found", None)
                
            # Update the bid status
            bid.status = "cancelled"
            bid.save()
            
            return RepositoryResponse(True, "Bid rejected by administrator", bid)
            
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, f"Failed to reject bid: {str(e)}", None)
            
    def admin_mark_bid_as_won(self, bid_id: int, admin_user: User) -> RepositoryResponse:
        """
        Admin marks a bid as won
        """
        try:
            # Verify the user is an admin
            if not admin_user.is_staff and not admin_user.is_superuser:
                return RepositoryResponse(False, "Only administrators can mark bids as won", None)
                
            # Get the bid regardless of owner
            bid = Bid.objects.filter(id=bid_id).first()
            if not bid:
                return RepositoryResponse(False, "Bid not found", None)
                
            # Update the bid status
            bid.status = "won"
            bid.save()
            
            # Mark other bids for this ad as lost
            Bid.objects.filter(ad=bid.ad).exclude(id=bid.id).update(status="lost")
            
            return RepositoryResponse(True, "Bid marked as won by administrator", bid)
            
        except Exception as e:
            logging_service.log_error(e)
            return RepositoryResponse(False, f"Failed to mark bid as won: {str(e)}", None)
        
    



