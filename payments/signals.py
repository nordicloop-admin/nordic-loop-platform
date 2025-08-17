from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from bids.models import Bid
from .models import PaymentIntent, Transaction
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Bid)
def handle_bid_won(sender, instance, created, **kwargs):
    """
    Signal handler for when a bid status changes to 'won'
    Triggers payment processing automatically
    """
    if not created and instance.status == 'won':
        # Check if payment intent already exists
        if hasattr(instance, 'payment_intent'):
            logger.info(f"Payment intent already exists for bid {instance.id}")
            return
        
        try:
            # Import here to avoid circular imports
            from .processors import BidPaymentProcessor
            
            processor = BidPaymentProcessor()
            result = processor.process_winning_bid(instance)
            
            if result['success']:
                logger.info(f"Payment processing initiated for winning bid {instance.id}")
            else:
                logger.error(f"Failed to initiate payment for winning bid {instance.id}: {result['message']}")
                
        except Exception as e:
            logger.error(f"Error processing payment for winning bid {instance.id}: {str(e)}")


@receiver(post_save, sender=PaymentIntent)
def handle_payment_intent_status_change(sender, instance, created, **kwargs):
    """
    Signal handler for payment intent status changes
    """
    if not created:
        # Check if status changed to succeeded
        if instance.status == 'succeeded' and not instance.confirmed_at:
            instance.confirmed_at = timezone.now()
            instance.save(update_fields=['confirmed_at'])
            
            # Create commission transaction
            try:
                Transaction.objects.create(
                    payment_intent=instance,
                    transaction_type='commission',
                    amount=instance.commission_amount,
                    currency=instance.currency,
                    status='completed',
                    from_user=instance.buyer,
                    to_user=None,  # Platform commission
                    description=f"Commission from payment {instance.stripe_payment_intent_id}",
                    processed_at=timezone.now()
                )
                
                # Create seller transaction (pending payout)
                Transaction.objects.create(
                    payment_intent=instance,
                    transaction_type='payout',
                    amount=instance.seller_amount,
                    currency=instance.currency,
                    status='pending',
                    from_user=None,  # Platform
                    to_user=instance.seller,
                    description=f"Seller payout from payment {instance.stripe_payment_intent_id}"
                )
                
                logger.info(f"Created commission and payout transactions for payment {instance.stripe_payment_intent_id}")
                
            except Exception as e:
                logger.error(f"Error creating transactions for payment {instance.stripe_payment_intent_id}: {str(e)}")


@receiver(pre_save, sender=Transaction)
def handle_transaction_status_change(sender, instance, **kwargs):
    """
    Signal handler for transaction status changes
    """
    if instance.pk:
        try:
            old_instance = Transaction.objects.get(pk=instance.pk)
            if old_instance.status != instance.status and instance.status == 'completed':
                instance.processed_at = timezone.now()
        except Transaction.DoesNotExist:
            pass


# Signal for creating notifications when payments are processed
@receiver(post_save, sender=PaymentIntent)
def create_payment_notifications(sender, instance, created, **kwargs):
    """
    Create notifications for payment events
    """
    if not created and instance.status == 'succeeded':
        try:
            # Import here to avoid circular imports
            from notifications.models import Notification
            
            # Notify buyer of successful payment
            Notification.objects.create(
                user=instance.buyer,
                title="Payment Successful",
                message=f"Your payment of {instance.total_amount} {instance.currency} for bid #{instance.bid.id} has been processed successfully.",
                type='payment',
                priority='normal',
                metadata={
                    'payment_intent_id': str(instance.id),
                    'bid_id': instance.bid.id,
                    'amount': str(instance.total_amount),
                    'commission': str(instance.commission_amount)
                }
            )
            
            # Notify seller of incoming payment (pending payout)
            Notification.objects.create(
                user=instance.seller,
                title="Payment Received",
                message=f"You have received a payment of {instance.seller_amount} {instance.currency} for your material. Payout will be processed according to schedule.",
                type='payment',
                priority='normal',
                metadata={
                    'payment_intent_id': str(instance.id),
                    'bid_id': instance.bid.id,
                    'seller_amount': str(instance.seller_amount),
                    'commission_rate': str(instance.commission_rate)
                }
            )
            
            logger.info(f"Created payment notifications for payment {instance.stripe_payment_intent_id}")
            
        except Exception as e:
            logger.error(f"Error creating payment notifications: {str(e)}")
