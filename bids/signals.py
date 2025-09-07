"""
Bid signals for handling auction winner notifications

This module contains Django signals that automatically trigger winner notifications
when bid statuses change to 'won', ensuring notifications work for both automatic
and manual auction closure scenarios.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.db.models import Q
from django.dispatch import receiver
from .models import Bid
from notifications.models import Notification
from notifications.templates import AuctionNotificationTemplates, BidNotificationTemplates, get_auction_notification_metadata, get_bid_notification_metadata

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Bid)
def store_previous_bid_status(sender, instance, **kwargs):
    """
    Store the previous bid status before saving to detect status changes
    """
    if instance.pk:
        try:
            previous_bid = Bid.objects.get(pk=instance.pk)
            instance._previous_status = previous_bid.status
        except Bid.DoesNotExist:
            instance._previous_status = None
    else:
        instance._previous_status = None


@receiver(post_save, sender=Bid)
def handle_bid_status_changes(sender, instance, created, **kwargs):
    """
    Handle bid status changes and send notifications when appropriate
    
    This signal is triggered after a bid is saved and handles:
    1. Winner notifications when bid status changes to 'won'
    2. Outbid notifications when bid status changes to 'outbid' or 'lost'
    """
    if created:
        # New bid created - handle new bid notifications if needed
        return
    
    # Get previous status
    previous_status = getattr(instance, '_previous_status', None)
    current_status = instance.status
    
    # Only process if status actually changed
    if previous_status == current_status:
        return
    
    try:
        # Handle winner notifications
        if current_status == 'won' and previous_status != 'won':
            _send_winner_notification_signal(instance)

        # Handle payment completion notifications
        elif current_status == 'paid' and previous_status == 'won':
            # Skip sending payment completion notification if winner notification already mentions automatic payment processing
            existing_winner_notification = Notification.objects.filter(
                user=instance.user,
                type='auction',
                title__icontains='Congratulations',
                message__icontains='Payment has been automatically processed'
            ).filter(
                Q(metadata__bid_id=instance.id) | 
                Q(metadata__auction_id=instance.ad.id)
            ).first()
            
            if not existing_winner_notification:
                _send_payment_completion_notification_signal(instance)

        # Handle outbid notifications
        elif current_status in ['outbid', 'lost'] and previous_status in ['active', 'winning']:
            _send_outbid_notification_signal(instance, previous_status)
            
    except Exception as e:
        logger.error(f"Error handling bid status change for bid {instance.id}: {str(e)}")


def _send_winner_notification_signal(winning_bid: Bid):
    """
    Send winner notification via signal (backup to service method)
    
    This is a backup notification method that ensures winner notifications
    are sent even if the service method fails or isn't called.
    """
    try:
        auction = winning_bid.ad
        
        # Check if ANY auction-related notification already exists for this user and bid to avoid duplicates
        existing_notification = Notification.objects.filter(
            user=winning_bid.user,
            type='auction',
            title__icontains='Congratulations'
        ).filter(
            Q(metadata__bid_id=winning_bid.id) | 
            Q(metadata__auction_id=auction.id)
        ).first()
        
        if existing_notification:
            logger.info(f"Winner notification already exists for bid {winning_bid.id}, skipping signal notification")
            return
        
        # Create winner notification using template with automatic payment message
        template = AuctionNotificationTemplates.winner_signal_backup(
            auction.title,
            winning_bid.bid_price_per_unit,
            auction.currency,
            winning_bid.volume_requested,
            auction.unit_of_measurement,
            winning_bid.total_bid_value
        )

        metadata = get_auction_notification_metadata(
            auction.id,
            winning_bid.id,
            winning_bid.bid_price_per_unit,
            winning_bid.volume_requested,
            winning_bid.total_bid_value,
            auction.currency,
            auction.unit_of_measurement,
            'signal_backup',
            'auction_won'
        )

        Notification.objects.create(
            user=winning_bid.user,
            title=template['title'],
            message=template['message'],
            type='auction',
            priority='high',
            metadata=metadata
        )
        
        logger.info(f"Winner notification sent via signal for bid {winning_bid.id}")
        
    except Exception as e:
        logger.error(f"Error sending winner notification via signal for bid {winning_bid.id}: {str(e)}")


def _send_outbid_notification_signal(outbid_bid: Bid, previous_status: str):
    """
    Send outbid notification to inform users they've been outbid
    """
    try:
        auction = outbid_bid.ad
        
        # Only send outbid notifications for active auctions
        if not auction.is_active or auction.status != 'active':
            return
        
        # Check if notification already exists to avoid duplicates
        existing_notification = Notification.objects.filter(
            user=outbid_bid.user,
            type='bid',
            metadata__bid_id=outbid_bid.id,
            metadata__action_type='outbid'
        ).exists()
        
        if existing_notification:
            return
        
        # Create outbid notification using template
        if outbid_bid.status == 'outbid':
            template = AuctionNotificationTemplates.outbid_notification(
                auction.title,
                outbid_bid.bid_price_per_unit,
                auction.currency,
                auction.unit_of_measurement
            )
        else:  # status == 'lost'
            template = AuctionNotificationTemplates.auction_ended_lost(
                auction.title,
                outbid_bid.bid_price_per_unit,
                auction.currency,
                auction.unit_of_measurement
            )

        metadata = get_bid_notification_metadata(
            auction.id,
            outbid_bid.id,
            outbid_bid.bid_price_per_unit,
            outbid_bid.volume_requested,
            auction.currency,
            auction.unit_of_measurement,
            'outbid',
            previous_status=previous_status,
            new_status=outbid_bid.status
        )

        Notification.objects.create(
            user=outbid_bid.user,
            title=template['title'],
            message=template['message'],
            type='bid',
            priority='normal',
            metadata=metadata
        )
        
        logger.info(f"Outbid notification sent for bid {outbid_bid.id}")

    except Exception as e:
        logger.error(f"Error sending outbid notification for bid {outbid_bid.id}: {str(e)}")


def _send_payment_completion_notification_signal(paid_bid: Bid):
    """
    Send payment completion notification to both buyer and seller
    """
    try:
        auction = paid_bid.ad

        # Send buyer confirmation notification
        buyer_title = "✅ Payment Confirmed!"
        buyer_message = (
            f"Your payment for {auction.title} has been successfully processed. "
            f"The seller has been notified and will coordinate delivery/pickup with you. "
            f"You can view your transaction history in your payments dashboard."
        )

        Notification.objects.create(
            user=paid_bid.user,
            title=buyer_title,
            message=buyer_message,
            type='payment',
            priority='high',
            action_url='/dashboard/payments',
            metadata={
                'auction_id': auction.id,
                'bid_id': paid_bid.id,
                'total_value': str(paid_bid.total_bid_value),
                'currency': auction.currency,
                'unit': auction.unit_of_measurement,
                'volume': str(paid_bid.volume_requested),
                'action_type': 'payment_confirmed'
            }
        )

        # Send seller payment received notification
        seller_title = "💰 Payment Received!"
        seller_message = (
            f"Payment has been received for your auction '{auction.title}'. "
            f"The buyer ({paid_bid.user.email}) has completed their payment. "
            f"Please coordinate delivery/pickup with the buyer. "
            f"Your payout will be processed according to the payout schedule."
        )

        Notification.objects.create(
            user=auction.user,
            title=seller_title,
            message=seller_message,
            type='payment',
            priority='high',
            action_url='/dashboard/payments',
            metadata={
                'auction_id': auction.id,
                'bid_id': paid_bid.id,
                'buyer_id': paid_bid.user.id,
                'buyer_email': paid_bid.user.email,
                'total_value': str(paid_bid.total_bid_value),
                'currency': auction.currency,
                'unit': auction.unit_of_measurement,
                'volume': str(paid_bid.volume_requested),
                'action_type': 'payment_received'
            }
        )

        logger.info(f"Payment completion notifications sent for bid {paid_bid.id}")

    except Exception as e:
        logger.error(f"Error sending payment completion notifications for bid {paid_bid.id}: {str(e)}")
