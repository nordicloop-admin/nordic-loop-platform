from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from company.models import Company
from notifications.models import Notification

User = get_user_model()

@receiver(post_save, sender=Company)
def notify_admin_new_company(sender, instance: Company, created: bool, **kwargs):
    """Create an admin notification whenever a new company registers."""
    if not created:
        return

    # Fetch admin users (using role field or Django is_staff/is_superuser flags)
    admin_users = User.objects.filter(role='Admin')
    if not admin_users.exists():
        # Fallback to superusers if no role-based admins found
        admin_users = User.objects.filter(is_superuser=True)

    # Common notification payload
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

    # Create individual notifications for each admin so they show in their own feeds
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
    if notifications:
        Notification.objects.bulk_create(notifications)
