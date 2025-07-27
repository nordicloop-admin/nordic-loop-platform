from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Subscription
from notifications.models import Notification

User = get_user_model()

@receiver(pre_save, sender=Subscription)
def track_subscription_changes(sender, instance, **kwargs):
    """
    Track subscription changes before saving to compare with previous state
    """
    if instance.pk:
        try:
            instance._previous_subscription = Subscription.objects.get(pk=instance.pk)
        except Subscription.DoesNotExist:
            instance._previous_subscription = None
    else:
        instance._previous_subscription = None

@receiver(post_save, sender=Subscription)
def notify_subscription_changes(sender, instance, created, **kwargs):
    """
    Send notifications when subscription status changes
    """
    # Get the company's users (assuming company has users)
    if not instance.company:
        return
    
    # Get all users associated with this company
    company_users = User.objects.filter(company=instance.company)
    
    if created:
        # New subscription created
        for user in company_users:
            Notification.objects.create(
                user=user,
                title="Subscription Activated",
                message=f"Your {instance.get_plan_display()} subscription has been successfully activated. You now have access to all premium features.",
                type='subscription',
                priority='normal',
                metadata={
                    'subscription_id': instance.id,
                    'plan': instance.plan,
                    'status': instance.status,
                    'start_date': instance.start_date.isoformat(),
                    'end_date': instance.end_date.isoformat()
                }
            )
    else:
        # Existing subscription updated
        previous = getattr(instance, '_previous_subscription', None)
        if not previous:
            return
        
        # Check for status changes
        if previous.status != instance.status:
            status_notifications = {
                'active': {
                    'title': 'Subscription Reactivated',
                    'message': f'Your {instance.get_plan_display()} subscription has been reactivated. Welcome back!',
                    'priority': 'normal'
                },
                'expired': {
                    'title': 'Subscription Expired',
                    'message': f'Your {instance.get_plan_display()} subscription has expired. Please renew to continue accessing premium features.',
                    'priority': 'high'
                },
                'payment_failed': {
                    'title': 'Payment Failed',
                    'message': f'Payment for your {instance.get_plan_display()} subscription failed. Please update your payment method to avoid service interruption.',
                    'priority': 'urgent'
                }
            }
            
            notification_config = status_notifications.get(instance.status)
            if notification_config:
                for user in company_users:
                    Notification.objects.create(
                        user=user,
                        title=notification_config['title'],
                        message=notification_config['message'],
                        type='subscription',
                        priority=notification_config['priority'],
                        metadata={
                            'subscription_id': instance.id,
                            'plan': instance.plan,
                            'previous_status': previous.status,
                            'new_status': instance.status,
                            'change_type': 'status_change'
                        }
                    )
        
        # Check for plan changes
        if previous.plan != instance.plan:
            plan_change_type = 'upgrade' if _is_plan_upgrade(previous.plan, instance.plan) else 'downgrade'
            
            for user in company_users:
                Notification.objects.create(
                    user=user,
                    title=f"Subscription {plan_change_type.title()}",
                    message=f"Your subscription has been {plan_change_type}d from {previous.get_plan_display()} to {instance.get_plan_display()}. Changes will take effect immediately.",
                    type='subscription',
                    priority='normal',
                    metadata={
                        'subscription_id': instance.id,
                        'previous_plan': previous.plan,
                        'new_plan': instance.plan,
                        'change_type': 'plan_change',
                        'upgrade_or_downgrade': plan_change_type
                    }
                )
        
        # Check for auto-renewal changes
        if previous.auto_renew != instance.auto_renew:
            auto_renew_message = (
                "Auto-renewal has been enabled for your subscription. Your subscription will automatically renew before expiration."
                if instance.auto_renew else
                "Auto-renewal has been disabled for your subscription. Please remember to manually renew before expiration."
            )
            
            for user in company_users:
                Notification.objects.create(
                    user=user,
                    title="Auto-Renewal Settings Updated",
                    message=auto_renew_message,
                    type='subscription',
                    priority='low',
                    metadata={
                        'subscription_id': instance.id,
                        'auto_renew': instance.auto_renew,
                        'change_type': 'auto_renew_change'
                    }
                )
        
        # Check for approaching expiration (if end_date changed and is within 7 days)
        if previous.end_date != instance.end_date:
            from datetime import datetime, timedelta
            from django.utils import timezone
            
            days_until_expiration = (instance.end_date - timezone.now().date()).days
            
            if 0 <= days_until_expiration <= 7 and instance.status == 'active':
                for user in company_users:
                    Notification.objects.create(
                        user=user,
                        title="Subscription Expiring Soon",
                        message=f"Your {instance.get_plan_display()} subscription will expire in {days_until_expiration} day{'s' if days_until_expiration != 1 else ''}. Please renew to avoid service interruption.",
                        type='subscription',
                        priority='high' if days_until_expiration <= 3 else 'normal',
                        metadata={
                            'subscription_id': instance.id,
                            'days_until_expiration': days_until_expiration,
                            'expiration_date': instance.end_date.isoformat(),
                            'change_type': 'expiration_warning'
                        }
                    )

def _is_plan_upgrade(old_plan, new_plan):
    """
    Determine if the plan change is an upgrade or downgrade
    """
    plan_hierarchy = {
        'free': 0,
        'standard': 1,
        'premium': 2
    }
    
    old_level = plan_hierarchy.get(old_plan, 0)
    new_level = plan_hierarchy.get(new_plan, 0)
    
    return new_level > old_level

# Admin notification for subscription changes
@receiver(post_save, sender=Subscription)
def notify_admin_subscription_changes(sender, instance, created, **kwargs):
    """
    Send notifications to admin users when subscription changes occur
    """
    # Get admin users
    admin_users = User.objects.filter(is_staff=True, role='Admin')
    
    if created:
        # New subscription created - notify admins
        for admin_user in admin_users:
            Notification.objects.create(
                user=admin_user,
                title="New Subscription Created",
                message=f"A new {instance.get_plan_display()} subscription has been created for {instance.company.official_name}.",
                type='admin',
                priority='low',
                metadata={
                    'subscription_id': instance.id,
                    'company_id': instance.company.id,
                    'company_name': instance.company.official_name,
                    'plan': instance.plan,
                    'status': instance.status,
                    'action_type': 'subscription_created'
                }
            )
    else:
        # Check for significant status changes that admins should know about
        previous = getattr(instance, '_previous_subscription', None)
        if previous and previous.status != instance.status:
            if instance.status in ['expired', 'payment_failed']:
                for admin_user in admin_users:
                    Notification.objects.create(
                        user=admin_user,
                        title=f"Subscription {instance.get_status_display()}",
                        message=f"{instance.company.official_name}'s {instance.get_plan_display()} subscription status changed to {instance.get_status_display()}.",
                        type='admin',
                        priority='normal',
                        metadata={
                            'subscription_id': instance.id,
                            'company_id': instance.company.id,
                            'company_name': instance.company.official_name,
                            'previous_status': previous.status,
                            'new_status': instance.status,
                            'action_type': 'subscription_status_change'
                        }
                    )
