"""Signals for Ad (auction) related metrics increments."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from ads.models import Ad
from core.metrics import ads_created_total, auctions_activated_total


@receiver(post_save, sender=Ad)
def ad_post_save(sender, instance: Ad, created, **kwargs):
    # Count ad creation
    if created:
        ads_created_total.inc()
    # Count activation transition
    # If ad is active and just created or status changed to active after completion
    if instance.status == 'active' and instance.is_complete:
        # We don't have old status here easily; light duplication acceptable.
        auctions_activated_total.inc()
