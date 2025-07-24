from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Q

from ads.models import Ad
from notifications.models import Notification
from .models import CategorySubscription

@receiver(post_save, sender=Ad)
def notify_category_subscribers(sender, instance, created, **kwargs):
    """
    Send notifications to users who are subscribed to the category or subcategory
    of a newly created and activated ad.
    """
    # Only send notifications for newly created ads that are active
    if created and instance.is_active:
        notify_subscribers_for_ad(instance)
    # Also handle when an ad becomes active after creation
    elif not created and instance.is_active and instance.tracker.has_changed('is_active') and instance.tracker.previous('is_active') is False:
        notify_subscribers_for_ad(instance)

def notify_subscribers_for_ad(ad):
    """
    Create notifications for all users subscribed to the ad's category or subcategory
    """
    if not ad.category:
        return
    
    # Find all users subscribed to this category or subcategory
    query = Q(category=ad.category)
    
    if ad.subcategory:
        # Include users subscribed to this specific subcategory
        query |= Q(category=ad.category, subcategory=ad.subcategory)
    
    # Get unique users who have subscribed
    subscriptions = CategorySubscription.objects.filter(query).select_related('user').distinct('user')
    
    # Create a notification for each subscribed user
    for subscription in subscriptions:
        user = subscription.user
        
        # Skip notification if the user is the one who created the ad
        if user == ad.user:
            continue
        
        # Create the notification
        category_name = ad.subcategory.name if ad.subcategory else ad.category.name
        
        Notification.objects.create(
            user=user,
            title=f"New {category_name} Auction Available",
            message=f"A new auction for {ad.title} has been posted in the {category_name} category that you're subscribed to.",
            type='auction'
        )
