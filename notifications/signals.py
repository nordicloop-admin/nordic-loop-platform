from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()

@receiver(pre_save, sender=User)
def track_user_changes(sender, instance, **kwargs):
    """
    Track user changes before saving to compare with previous state
    """
    if instance.pk:
        try:
            instance._previous_user = User.objects.get(pk=instance.pk)
        except User.DoesNotExist:
            instance._previous_user = None
    else:
        instance._previous_user = None

@receiver(post_save, sender=User)
def notify_user_account_changes(sender, instance, created, **kwargs):
    """
    Send notifications when important user account changes occur
    """
    if created:
        # Welcome notification for new users
        Notification.objects.create(
            user=instance,
            title="Welcome to Nordic Loop!",
            message="Welcome to Nordic Loop! Your account has been successfully created. Start exploring our marketplace and create your first auction.",
            type='welcome',
            priority='normal',
            metadata={
                'user_id': instance.id,
                'action_type': 'account_created'
            }
        )
    else:
        # Check for important changes
        previous = getattr(instance, '_previous_user', None)
        if not previous:
            return

        # Check for password changes
        if previous.password != instance.password:
            Notification.objects.create(
                user=instance,
                title="Password Changed",
                message="Your password has been successfully changed. If you didn't make this change, please contact support immediately.",
                type='security',
                priority='high',
                metadata={
                    'user_id': instance.id,
                    'action_type': 'password_change'
                }
            )

        # Check for email changes
        if previous.email != instance.email:
            Notification.objects.create(
                user=instance,
                title="Email Address Updated",
                message=f"Your email address has been updated to {instance.email}. Please verify your new email address.",
                type='account',
                priority='normal',
                metadata={
                    'user_id': instance.id,
                    'previous_email': previous.email,
                    'new_email': instance.email,
                    'action_type': 'email_change'
                }
            )

        # Check for role changes
        if hasattr(previous, 'role') and hasattr(instance, 'role') and previous.role != instance.role:
            Notification.objects.create(
                user=instance,
                title="Account Role Updated",
                message=f"Your account role has been updated to {instance.role}. You may now have access to additional features.",
                type='account',
                priority='normal',
                metadata={
                    'user_id': instance.id,
                    'previous_role': previous.role,
                    'new_role': instance.role,
                    'action_type': 'role_change'
                }
            )

# You can add more signal handlers here for automatic notification creation
# For example, you might want to create notifications when certain events happen
# in your application, like when a new bid is placed or an ad is approved.
