"""Signals for Company registration metrics increments and admin notifications."""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from notifications.models import Notification
from company.models import Company
from core.metrics import companies_registered_total

User = get_user_model()


@receiver(post_save, sender=Company)
def company_post_save(sender, instance: Company, created: bool, **kwargs):
    """Increment metrics and notify admins when a company is first created."""
    if not created:
        return

    # Increment business counter
    companies_registered_total.inc()

    # Find admin users by role, fallback to superusers
    admin_users = User.objects.filter(role='Admin')
    if not admin_users.exists():
        admin_users = User.objects.filter(is_superuser=True)

    if not admin_users.exists():
        return  # No admins to notify

    title = "New Company Registration"
    message = (
        f"Company '{instance.official_name}' has registered and is pending approval. "
        f"VAT: {instance.vat_number} | Email: {instance.email} | Country: {instance.country}"
    )
    metadata = {
        'company_id': instance.id,
        'official_name': instance.official_name,
        'vat_number': instance.vat_number,
        'status': instance.status,
        'action_type': 'company_registration'
    }

    notifications = [
        Notification(
            user=admin,
            title=title,
            message=message,
            type='admin',
            priority='high',
            metadata=metadata
        ) for admin in admin_users
    ]
    Notification.objects.bulk_create(notifications)
