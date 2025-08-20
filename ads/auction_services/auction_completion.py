"""
Auction Completion Service

This service handles the automatic closure of expired auctions and winner notifications.
It provides methods for:
1. Finding auctions that have passed their end date
2. Determining the highest bidder for each auction
3. Marking winning bids and updating auction status
4. Sending notifications to winners
5. Handling both automatic and manual auction closure scenarios
"""

import logging
from datetime import timedelta
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from ads.models import Ad
from bids.models import Bid
from notifications.models import Notification
from notifications.templates import AuctionNotificationTemplates, get_auction_notification_metadata
from base.services.logging import LoggingService

logger = logging.getLogger(__name__)
logging_service = LoggingService()


class AuctionCompletionService:
    """Service for handling auction completion and winner notifications"""
    
    def get_expired_auctions(self, grace_period_minutes: int = 5) -> List[Ad]:
        """
        Find auctions that have passed their end date and are ready to be closed
        
        Args:
            grace_period_minutes: Grace period in minutes after auction end time
            
        Returns:
            List of Ad objects that are expired and ready to close
        """
        try:
            # Calculate cutoff time with grace period
            cutoff_time = timezone.now() - timedelta(minutes=grace_period_minutes)
            
            # Find active auctions that have passed their end date
            expired_auctions = Ad.objects.filter(
                is_active=True,
                is_complete=True,  # Only complete ads can have active auctions
                auction_end_date__isnull=False,
                auction_end_date__lte=cutoff_time,
                status='active'  # Not suspended
            ).select_related('user', 'category', 'subcategory', 'location')
            
            return list(expired_auctions)
            
        except Exception as e:
            logging_service.log_error(e)
            logger.error(f"Error finding expired auctions: {str(e)}")
            return []
    
    def close_auction_with_notifications(self, auction: Ad) -> Dict[str, Any]:
        """
        Close an auction and send winner notifications
        
        Args:
            auction: The Ad object representing the auction to close
            
        Returns:
            Dictionary with closure results and notification status
        """
        try:
            with transaction.atomic():
                # Get the highest bid for this auction
                highest_bid = self._get_highest_bid_for_auction(auction)
                
                result = {
                    'success': False,
                    'auction_id': auction.id,
                    'auction_title': auction.title or f"Auction #{auction.id}",
                    'currency': auction.currency,
                    'unit': auction.unit_of_measurement,
                    'has_winner': False,
                    'notification_sent': False
                }
                
                if not highest_bid:
                    # No bids received - close auction without winner
                    self._close_auction_without_winner(auction)
                    result.update({
                        'success': True,
                        'message': 'Auction closed - no bids received',
                        'has_winner': False
                    })
                    return result
                
                # Check if reserve price is met (if set)
                if auction.reserve_price and highest_bid.bid_price_per_unit < auction.reserve_price:
                    # Reserve price not met - close auction without winner
                    self._close_auction_without_winner(auction)
                    result.update({
                        'success': True,
                        'message': 'Auction closed - reserve price not met',
                        'has_winner': False,
                        'reserve_price': auction.reserve_price,
                        'highest_bid': highest_bid.bid_price_per_unit
                    })
                    return result
                
                # Reserve price met or no reserve - auction successful
                success = self._close_auction_with_winner(auction, highest_bid)
                
                if success:
                    # Send winner notification
                    notification_sent = self._send_winner_notification(
                        auction, highest_bid, closure_type='automatic'
                    )
                    
                    result.update({
                        'success': True,
                        'message': 'Auction completed successfully',
                        'has_winner': True,
                        'winner_email': highest_bid.user.email,
                        'winning_price': highest_bid.bid_price_per_unit,
                        'winning_volume': highest_bid.volume_requested,
                        'notification_sent': notification_sent
                    })
                else:
                    result.update({
                        'success': False,
                        'message': 'Failed to close auction with winner'
                    })
                
                return result
                
        except Exception as e:
            logging_service.log_error(e)
            logger.error(f"Error closing auction {auction.id}: {str(e)}")
            return {
                'success': False,
                'auction_id': auction.id,
                'auction_title': auction.title or f"Auction #{auction.id}",
                'message': f'Error closing auction: {str(e)}'
            }
    
    def close_auction_manually(self, auction: Ad, winning_bid: Bid) -> Dict[str, Any]:
        """
        Close an auction manually (e.g., by admin) with a specific winning bid
        
        Args:
            auction: The Ad object representing the auction
            winning_bid: The Bid object that should be marked as winner
            
        Returns:
            Dictionary with closure results and notification status
        """
        try:
            with transaction.atomic():
                success = self._close_auction_with_winner(auction, winning_bid)
                
                if success:
                    # Send winner notification for manual closure
                    notification_sent = self._send_winner_notification(
                        auction, winning_bid, closure_type='manual'
                    )
                    
                    return {
                        'success': True,
                        'message': 'Auction closed manually with winner',
                        'has_winner': True,
                        'winner_email': winning_bid.user.email,
                        'winning_price': winning_bid.bid_price_per_unit,
                        'winning_volume': winning_bid.volume_requested,
                        'notification_sent': notification_sent
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Failed to close auction manually'
                    }
                    
        except Exception as e:
            logging_service.log_error(e)
            logger.error(f"Error manually closing auction {auction.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error closing auction manually: {str(e)}'
            }
    
    def _get_highest_bid_for_auction(self, auction: Ad) -> Optional[Bid]:
        """Get the highest active bid for an auction"""
        try:
            return Bid.objects.filter(
                ad=auction,
                status__in=['active', 'winning']
            ).order_by('-bid_price_per_unit', 'created_at').first()
        except Exception:
            return None
    
    def _close_auction_without_winner(self, auction: Ad) -> bool:
        """Close auction without a winner (no bids or reserve not met)"""
        try:
            # Mark all bids as lost
            Bid.objects.filter(ad=auction, status__in=['active', 'winning']).update(status='lost')

            # Update auction status
            auction.is_active = False
            auction.status = 'completed'
            auction.save()

            return True
        except Exception as e:
            logging_service.log_error(e)
            return False
    
    def _close_auction_with_winner(self, auction: Ad, winning_bid: Bid) -> bool:
        """Close auction with a winner"""
        try:
            # Mark winning bid as won
            winning_bid.status = 'won'
            winning_bid.save()

            # Mark all other bids as lost
            Bid.objects.filter(
                ad=auction,
                status__in=['active', 'winning', 'outbid']
            ).exclude(id=winning_bid.id).update(status='lost')

            # Update auction status
            auction.is_active = False
            auction.status = 'completed'
            auction.save()

            return True
        except Exception as e:
            logging_service.log_error(e)
            return False
    
    def _send_winner_notification(self, auction: Ad, winning_bid: Bid, closure_type: str = 'automatic') -> bool:
        """Send notification to the winning bidder"""
        try:
            # Get notification template based on closure type
            if closure_type == 'manual':
                template = AuctionNotificationTemplates.winner_manual_closure(
                    auction.title,
                    winning_bid.bid_price_per_unit,
                    auction.currency,
                    winning_bid.volume_requested,
                    auction.unit_of_measurement
                )
            else:
                template = AuctionNotificationTemplates.winner_automatic_closure(
                    auction.title,
                    winning_bid.bid_price_per_unit,
                    auction.currency,
                    winning_bid.volume_requested,
                    auction.unit_of_measurement,
                    winning_bid.total_bid_value
                )

            # Generate metadata
            metadata = get_auction_notification_metadata(
                auction.id,
                winning_bid.id,
                winning_bid.bid_price_per_unit,
                winning_bid.volume_requested,
                winning_bid.total_bid_value,
                auction.currency,
                auction.unit_of_measurement,
                closure_type,
                'auction_won'
            )

            # Create the notification
            Notification.objects.create(
                user=winning_bid.user,
                title=template['title'],
                message=template['message'],
                type='auction',
                priority='high',
                metadata=metadata
            )
            
            logger.info(f"Winner notification sent for auction {auction.id} to user {winning_bid.user.email}")
            return True
            
        except Exception as e:
            logging_service.log_error(e)
            logger.error(f"Error sending winner notification for auction {auction.id}: {str(e)}")
            return False
