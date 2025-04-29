from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Auction, Bid


@receiver(post_save, sender=Bid)
def update_auction_current_price(sender, instance, created, **kwargs):
    """
    Update the auction's current price when a new bid is created.
    """
    if created and instance.amount > instance.auction.current_price:
        instance.auction.current_price = instance.amount
        instance.auction.save(update_fields=['current_price'])


@receiver(pre_save, sender=Auction)
def check_auction_end_date(sender, instance, **kwargs):
    """
    Check if an auction's end date has passed and update its status accordingly.
    """
    if instance.status == 'active' and instance.end_date <= timezone.now():
        instance.status = 'ended'


@receiver(post_save, sender=Auction)
def set_winning_bid_for_ended_auction(sender, instance, **kwargs):
    """
    Set the winning bid for an auction that has just ended.
    """
    if instance.status == 'ended':
        # Get the highest bid
        highest_bid = instance.bids.order_by('-amount').first()

        # Check if there are any bids and if the highest bid meets the reserve price
        if highest_bid and (not instance.reserve_price or highest_bid.amount >= instance.reserve_price):
            # Set the bid as winning
            highest_bid.is_winning = True
            highest_bid.save(update_fields=['is_winning'])
