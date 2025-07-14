from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Notification

# You can add signal handlers here for automatic notification creation
# For example, you might want to create notifications when certain events happen
# in your application, like when a new bid is placed or an ad is approved.

# Example signal handler (commented out):
# @receiver(post_save, sender=SomeModel)
# def create_notification_on_event(sender, instance, created, **kwargs):
#     if created:
#         Notification.objects.create(
#             title="New Event",
#             message=f"A new event has occurred: {instance}",
#             type="info",
#             user=instance.user  # Assuming the model has a user field
#         )
