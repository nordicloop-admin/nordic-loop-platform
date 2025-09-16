"""
Payment readiness utilities for marketplace functionality
"""
import stripe
from functools import wraps
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


def check_stripe_account_capabilities(stripe_account_id):
    """
    Check if a Stripe Connect account has the required capabilities
    
    Args:
        stripe_account_id (str): The Stripe account ID to check
        
    Returns:
        tuple: (is_ready, capabilities_status, error_message)
    """
    if not stripe_account_id:
        return False, {}, "No Stripe account ID found"
    
    try:
        account = stripe.Account.retrieve(stripe_account_id)
        
        required_capabilities = ['transfers', 'card_payments']
        capabilities_status = {}
        
        for capability in required_capabilities:
            status = account.capabilities.get(capability, 'inactive')
            capabilities_status[capability] = status
            
        # Check if all required capabilities are active
        all_ready = all(
            capabilities_status.get(cap) == 'active' 
            for cap in required_capabilities
        )
        
        return all_ready, capabilities_status, None
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error checking account {stripe_account_id}: {e}")
        return False, {}, str(e)
    except Exception as e:
        logger.error(f"Unexpected error checking account {stripe_account_id}: {e}")
        return False, {}, str(e)


def update_company_payment_status(company):
    """
    Update a company's payment readiness status by checking their Stripe account
    
    Args:
        company: Company model instance
        
    Returns:
        bool: Whether the company is payment ready
    """
    if not company.stripe_account_id:
        company.payment_ready = False
        company.stripe_capabilities_complete = False
        company.stripe_onboarding_complete = False
    else:
        is_ready, _, _ = check_stripe_account_capabilities(
            company.stripe_account_id
        )
        
        company.stripe_capabilities_complete = is_ready
        company.payment_ready = is_ready
        
        # Check if onboarding is complete (simplified check)
        company.stripe_onboarding_complete = is_ready
    
    company.last_payment_check = timezone.now()
    company.save(update_fields=[
        'payment_ready', 
        'stripe_capabilities_complete', 
        'stripe_onboarding_complete', 
        'last_payment_check'
    ])
    
    return company.payment_ready


def requires_payment_ready_company(f):
    """
    Decorator that ensures the user's company has payment setup complete
    before allowing auction-related operations.
    
    Usage:
        @requires_payment_ready_company
        def make_auction_active(request, auction_id):
            # This will only execute if company payment is ready
            pass
    """
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            raise PermissionDenied("Authentication required")
            
        if not hasattr(request.user, 'company') or not request.user.company:
            raise PermissionDenied("Company association required")
            
        company = request.user.company
        
        # Check if we need to refresh the payment status
        should_refresh = (
            not company.last_payment_check or 
            company.last_payment_check < timezone.now() - timedelta(hours=24)
        )
        
        if should_refresh:
            update_company_payment_status(company)
            
        if not company.payment_ready:
            raise ValidationError(
                "Your company's payment setup is not complete. "
                "Please complete Stripe onboarding before publishing auctions."
            )
            
        return f(request, *args, **kwargs)
    
    return wrapper


def check_company_payment_readiness(company):
    """
    Simple function to check if a company is ready to receive payments
    
    Args:
        company: Company model instance
        
    Returns:
        bool: Whether the company can receive payments
    """
    if not company:
        return False
        
    # Check if we need to refresh the status
    should_refresh = (
        not company.last_payment_check or 
        company.last_payment_check < timezone.now() - timedelta(hours=24)
    )
    
    if should_refresh:
        return update_company_payment_status(company)
        
    return company.payment_ready


def validate_auction_publication(user):
    """
    Validate that a user can publish auctions (payment readiness check)
    
    Args:
        user: User model instance
        
    Raises:
        ValidationError: If user cannot publish auctions
        
    Returns:
        bool: True if validation passes
    """
    if not user.company:
        raise ValidationError("Company association required to publish auctions")
        
    if not check_company_payment_readiness(user.company):
        raise ValidationError(
            "Your company's payment setup is incomplete. "
            "Please complete Stripe Connect onboarding to publish auctions."
        )
        
    return True