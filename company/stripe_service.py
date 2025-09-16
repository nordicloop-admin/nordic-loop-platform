"""
Stripe Connect service for handling account onboarding and management
"""
import stripe
import logging
from django.conf import settings
from django.urls import reverse
from typing import Dict, Optional, Tuple
from .models import Company

# Configure Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')

logger = logging.getLogger(__name__)

class StripeConnectService:
    """Service for managing Stripe Connect accounts"""
    
    @staticmethod
    def create_express_account(company: Company, user_email: str, request=None) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        Create a Stripe Express account for a company and generate onboarding URL
        Returns: (success, message, account_id, onboarding_url)
        """
        try:
            # Create Stripe Express account
            account = stripe.Account.create(
                type='express',
                country='SE',  # Sweden - adjust based on your market
                email=user_email,
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
                business_type='company',
                metadata={
                    'company_id': str(company.id),
                    'company_name': company.official_name,
                }
            )
            
            # Save account ID to company
            company.stripe_account_id = account.id
            company.save()
            
            logger.info(f"Created Stripe Express account {account.id} for company {company.id}")
            
            # Immediately create onboarding URL if request is provided
            onboarding_url = None
            if request:
                try:
                    # Build return and refresh URLs - point to frontend, not backend
                    frontend_base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
                    return_url = f"{frontend_base_url}/dashboard/payments/complete"
                    refresh_url = f"{frontend_base_url}/dashboard/payments/setup"
                    
                    # Create account link for onboarding
                    account_link = stripe.AccountLink.create(
                        account=account.id,
                        refresh_url=refresh_url,
                        return_url=return_url,
                        type='account_onboarding',
                    )
                    onboarding_url = account_link.url
                    logger.info(f"Created onboarding URL for account {account.id}")
                except Exception as e:
                    logger.warning(f"Failed to create onboarding URL: {str(e)}")
            
            return True, "Account created successfully", account.id, onboarding_url
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating account for company {company.id}: {str(e)}")
            return False, f"Payment setup failed: {str(e)}", None, None
        except Exception as e:
            logger.error(f"Unexpected error creating account for company {company.id}: {str(e)}")
            return False, "An unexpected error occurred", None, None

    @staticmethod
    def create_account_link(company: Company, request) -> Tuple[bool, str, Optional[str]]:
        """
        Create an account link for onboarding
        Returns: (success, message, onboarding_url)
        """
        try:
            if not company.stripe_account_id:
                return False, "No Stripe account found. Please create an account first.", None
            
            # Build return and refresh URLs - point to frontend, not backend
            frontend_base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            return_url = f"{frontend_base_url}/dashboard/payments/complete"
            refresh_url = f"{frontend_base_url}/dashboard/payments/setup"
            
            # Create account link
            account_link = stripe.AccountLink.create(
                account=company.stripe_account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type='account_onboarding',
            )
            
            logger.info(f"Created onboarding link for account {company.stripe_account_id}")
            return True, "Onboarding link created", account_link.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating account link: {str(e)}")
            return False, f"Failed to create onboarding link: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error creating account link: {str(e)}")
            return False, "An unexpected error occurred", None

    @staticmethod
    def check_account_status(company: Company) -> Dict[str, any]:
        """
        Check the status of a Stripe Connect account
        Returns detailed account information
        """
        try:
            if not company.stripe_account_id:
                return {
                    'exists': False,
                    'charges_enabled': False,
                    'details_submitted': False,
                    'payouts_enabled': False,
                    'requirements': [],
                    'capabilities': {},
                }
            
            account = stripe.Account.retrieve(company.stripe_account_id)
            
            # Check capabilities status
            capabilities = {}
            for capability, status_info in account.capabilities.items():
                # Handle both object and string status formats
                if hasattr(status_info, 'status'):
                    capabilities[capability] = status_info.status
                else:
                    capabilities[capability] = status_info
            
            # Get requirements
            requirements = []
            if account.requirements:
                requirements = account.requirements.currently_due + account.requirements.eventually_due
            
            status_info = {
                'exists': True,
                'account_id': account.id,
                'charges_enabled': account.charges_enabled,
                'details_submitted': account.details_submitted,
                'payouts_enabled': account.payouts_enabled,
                'requirements': requirements,
                'capabilities': capabilities,
                'country': account.country,
                'email': account.email,
                'type': account.type,
            }
            
            # Update company payment status based on account status
            # Check for critical requirements (ignore document verification for now)
            critical_requirements = [req for req in requirements 
                                   if not req.endswith('.verification.document')]
            
            payment_ready = (
                account.charges_enabled and 
                account.payouts_enabled and 
                account.details_submitted and
                len(critical_requirements) == 0 and
                capabilities.get('card_payments') == 'active' and
                capabilities.get('transfers') == 'active'
            )
            
            # Update company fields
            company.payment_ready = payment_ready
            company.stripe_capabilities_complete = (
                capabilities.get('card_payments') == 'active' and
                capabilities.get('transfers') == 'active'
            )
            # Onboarding is complete if basic details are submitted (document verification can be pending)
            company.stripe_onboarding_complete = (
                account.details_submitted and 
                capabilities.get('card_payments') == 'active' and
                capabilities.get('transfers') == 'active'
            )
            company.save()
            
            logger.info(f"Updated account status for company {company.id}: payment_ready={payment_ready}")
            return status_info
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error checking account status: {str(e)}")
            return {'exists': False, 'error': str(e)}
        except Exception as e:
            logger.error(f"Unexpected error checking account status: {str(e)}")
            return {'exists': False, 'error': 'An unexpected error occurred'}

    @staticmethod
    def create_login_link(company: Company) -> Tuple[bool, str, Optional[str]]:
        """
        Create a login link for the Stripe Express dashboard
        Returns: (success, message, login_url)
        """
        try:
            if not company.stripe_account_id:
                return False, "No Stripe account found", None
            
            login_link = stripe.Account.create_login_link(company.stripe_account_id)
            
            logger.info(f"Created login link for account {company.stripe_account_id}")
            return True, "Login link created", login_link.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating login link: {str(e)}")
            return False, f"Failed to create dashboard link: {str(e)}", None
        except Exception as e:
            logger.error(f"Unexpected error creating login link: {str(e)}")
            return False, "An unexpected error occurred", None

    @staticmethod
    def handle_account_update_webhook(account_id: str) -> bool:
        """
        Handle account.updated webhook from Stripe
        Returns: True if processed successfully
        """
        try:
            # Find company with this account ID
            company = Company.objects.filter(stripe_account_id=account_id).first()
            if not company:
                logger.warning(f"No company found for Stripe account {account_id}")
                return False
            
            # Update account status
            StripeConnectService.check_account_status(company)
            logger.info(f"Processed account update webhook for account {account_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing account update webhook: {str(e)}")
            return False