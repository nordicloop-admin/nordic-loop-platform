"""
Payment Completion Service

This service handles post-payment processing for auction winners, including:
1. Updating bid and auction statuses after successful payment
2. Sending payment confirmation notifications to both buyer and seller
3. Triggering any additional post-payment workflows
"""

import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from bids.models import Bid
from ads.models import Ad
from notifications.models import Notification
from notifications.templates import AuctionNotificationTemplates, get_auction_notification_metadata
from ..models import PaymentIntent, Transaction
from base.services.logging import LoggingService

logger = logging.getLogger(__name__)
logging_service = LoggingService()


class PaymentCompletionService:
    """Service for handling payment completion workflows"""
    
    def process_payment_completion(self, payment_intent: PaymentIntent) -> Dict[str, Any]:
        """
        Process payment completion for an auction winner
        
        Args:
            payment_intent: The completed PaymentIntent object
            
        Returns:
            Dictionary with completion results and notification status
        """
        try:
            with transaction.atomic():
                # Get related objects
                winning_bid = payment_intent.bid
                auction = winning_bid.ad
                buyer = payment_intent.buyer
                seller = payment_intent.seller
                
                # Update bid status to 'paid'
                winning_bid.status = 'paid'
                winning_bid.save()
                
                # Create transaction record
                transaction_record = Transaction.objects.create(
                    payment_intent=payment_intent,
                    buyer=buyer,
                    seller=seller,
                    total_amount=payment_intent.total_amount,
                    commission_amount=payment_intent.commission_amount,
                    seller_amount=payment_intent.seller_amount,
                    currency=payment_intent.currency,
                    status='completed',
                    processed_at=timezone.now()
                )
                
                # Send notifications
                buyer_notification_sent = self._send_buyer_confirmation_notification(
                    auction, winning_bid, payment_intent
                )
                
                seller_notification_sent = self._send_seller_payment_notification(
                    auction, winning_bid, payment_intent
                )
                
                result = {
                    'success': True,
                    'message': 'Payment completion processed successfully',
                    'transaction_id': transaction_record.id,
                    'bid_id': winning_bid.id,
                    'auction_id': auction.id,
                    'buyer_notification_sent': buyer_notification_sent,
                    'seller_notification_sent': seller_notification_sent,
                    'total_amount': str(payment_intent.total_amount),
                    'currency': payment_intent.currency
                }
                
                logger.info(f"Payment completion processed for bid {winning_bid.id}, payment intent {payment_intent.id}")
                return result
                
        except Exception as e:
            logging_service.log_error(e)
            logger.error(f"Error processing payment completion for payment intent {payment_intent.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing payment completion: {str(e)}',
                'payment_intent_id': str(payment_intent.id)
            }
    
    def _send_buyer_confirmation_notification(self, auction: Ad, winning_bid: Bid, payment_intent: PaymentIntent) -> bool:
        """Send payment confirmation notification to the buyer"""
        try:
            title = "✅ Payment Confirmed!"
            message = (
                f"Your payment of {payment_intent.total_amount} {payment_intent.currency} "
                f"for {auction.title} has been successfully processed. "
                f"The seller has been notified and will coordinate delivery/pickup with you. "
                f"You can view your transaction history in your payments dashboard."
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
                'payment_confirmed',
                'payment_confirmation'
            )
            
            # Add payment-specific metadata
            metadata.update({
                'payment_intent_id': str(payment_intent.id),
                'transaction_amount': str(payment_intent.total_amount),
                'commission_amount': str(payment_intent.commission_amount),
                'seller_amount': str(payment_intent.seller_amount)
            })
            
            # Create the notification
            Notification.objects.create(
                user=winning_bid.user,
                title=title,
                message=message,
                type='payment',
                priority='high',
                action_url='/dashboard/payments',
                metadata=metadata
            )
            
            logger.info(f"Buyer confirmation notification sent for payment intent {payment_intent.id}")
            return True
            
        except Exception as e:
            logging_service.log_error(e)
            logger.error(f"Error sending buyer confirmation notification for payment intent {payment_intent.id}: {str(e)}")
            return False
    
    def _send_seller_payment_notification(self, auction: Ad, winning_bid: Bid, payment_intent: PaymentIntent) -> bool:
        """Send payment received notification to the seller"""
        try:
            title = "💰 Payment Received!"
            message = (
                f"Great news! Payment of {payment_intent.seller_amount} {payment_intent.currency} "
                f"has been received for your auction '{auction.title}'. "
                f"The buyer ({winning_bid.user.email}) has completed their payment. "
                f"Please coordinate delivery/pickup with the buyer. "
                f"Your payout will be processed according to the payout schedule."
            )
            
            # Generate metadata for seller
            metadata = {
                'auction_id': auction.id,
                'bid_id': winning_bid.id,
                'buyer_id': winning_bid.user.id,
                'buyer_email': winning_bid.user.email,
                'payment_intent_id': str(payment_intent.id),
                'seller_amount': str(payment_intent.seller_amount),
                'commission_amount': str(payment_intent.commission_amount),
                'total_amount': str(payment_intent.total_amount),
                'currency': payment_intent.currency,
                'unit': auction.unit_of_measurement,
                'volume': str(winning_bid.volume_requested),
                'action_type': 'payment_received'
            }
            
            # Create the notification
            Notification.objects.create(
                user=auction.user,
                title=title,
                message=message,
                type='payment',
                priority='high',
                action_url='/dashboard/payments',
                metadata=metadata
            )
            
            logger.info(f"Seller payment notification sent for payment intent {payment_intent.id}")
            return True
            
        except Exception as e:
            logging_service.log_error(e)
            logger.error(f"Error sending seller payment notification for payment intent {payment_intent.id}: {str(e)}")
            return False
    
    def handle_payment_failure(self, payment_intent: PaymentIntent, failure_reason: str) -> Dict[str, Any]:
        """
        Handle payment failure scenarios
        
        Args:
            payment_intent: The failed PaymentIntent object
            failure_reason: Reason for payment failure
            
        Returns:
            Dictionary with failure handling results
        """
        try:
            # Send failure notification to buyer
            failure_notification_sent = self._send_payment_failure_notification(
                payment_intent, failure_reason
            )
            
            result = {
                'success': True,
                'message': 'Payment failure handled',
                'payment_intent_id': str(payment_intent.id),
                'failure_reason': failure_reason,
                'failure_notification_sent': failure_notification_sent
            }
            
            logger.info(f"Payment failure handled for payment intent {payment_intent.id}: {failure_reason}")
            return result
            
        except Exception as e:
            logging_service.log_error(e)
            logger.error(f"Error handling payment failure for payment intent {payment_intent.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error handling payment failure: {str(e)}',
                'payment_intent_id': str(payment_intent.id)
            }
    
    def _send_payment_failure_notification(self, payment_intent: PaymentIntent, failure_reason: str) -> bool:
        """Send payment failure notification to the buyer"""
        try:
            winning_bid = payment_intent.bid
            auction = winning_bid.ad
            
            title = "❌ Payment Failed"
            message = (
                f"Your payment for {auction.title} could not be processed. "
                f"Reason: {failure_reason}. "
                f"Please try again or contact support if the issue persists. "
                f"You have 48 hours from winning the auction to complete payment."
            )
            
            # Generate metadata
            metadata = {
                'auction_id': auction.id,
                'bid_id': winning_bid.id,
                'payment_intent_id': str(payment_intent.id),
                'failure_reason': failure_reason,
                'total_amount': str(payment_intent.total_amount),
                'currency': payment_intent.currency,
                'action_type': 'payment_failed'
            }
            
            # Create the notification
            Notification.objects.create(
                user=winning_bid.user,
                title=title,
                message=message,
                type='payment',
                priority='urgent',
                action_url=f'/dashboard/winning-bids?bid_id={winning_bid.id}',
                metadata=metadata
            )
            
            logger.info(f"Payment failure notification sent for payment intent {payment_intent.id}")
            return True
            
        except Exception as e:
            logging_service.log_error(e)
            logger.error(f"Error sending payment failure notification for payment intent {payment_intent.id}: {str(e)}")
            return False
