"""
Stripe Subscription Service for handling subscription payments
"""
import stripe
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from users.models import User
from company.models import Company
from ads.models import Subscription
from pricing.models import PricingPlan

logger = logging.getLogger(__name__)


class StripeSubscriptionService:
    """
    Service for handling Stripe subscription payments
    """
    
    def __init__(self):
        self.stripe_api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not self.stripe_api_key:
            logger.warning("Stripe API key not configured")
        else:
            stripe.api_key = self.stripe_api_key
    
    def create_customer(self, user: User, company: Company) -> Dict[str, Any]:
        """
        Create a Stripe customer for a user/company
        """
        try:
            if not self.stripe_api_key:
                return {
                    'success': False,
                    'message': 'Stripe API key not configured'
                }
            
            # Check if customer already exists
            existing_customers = stripe.Customer.list(
                email=user.email,
                limit=1
            )
            
            if existing_customers.data:
                customer = existing_customers.data[0]
                logger.info(f"Found existing Stripe customer {customer.id} for {user.email}")
                return {
                    'success': True,
                    'customer_id': customer.id,
                    'customer': customer,
                    'message': 'Found existing customer'
                }
            
            # Create new customer
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip() or user.email,
                description=f"Customer for {company.official_name}",
                metadata={
                    'user_id': user.id,
                    'company_id': company.id,
                    'company_name': company.official_name
                }
            )
            
            logger.info(f"Created Stripe customer {customer.id} for {user.email}")
            return {
                'success': True,
                'customer_id': customer.id,
                'customer': customer,
                'message': 'Customer created successfully'
            }
            
        except stripe.StripeError as e:
            logger.error(f"Stripe error creating customer for {user.email}: {str(e)}")
            return {
                'success': False,
                'message': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error creating customer for {user.email}: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating customer: {str(e)}'
            }
    
    def create_subscription_checkout(self, user: User, company: Company, plan_type: str) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for subscription payment
        """
        try:
            if not self.stripe_api_key:
                return {
                    'success': False,
                    'message': 'Stripe API key not configured'
                }
            
            # Get pricing plan
            try:
                pricing_plan = PricingPlan.objects.get(plan_type=plan_type, is_active=True)
            except PricingPlan.DoesNotExist:
                return {
                    'success': False,
                    'message': f'Pricing plan "{plan_type}" not found'
                }
            
            # For free plan, no payment needed
            if pricing_plan.price == 0:
                return self._create_free_subscription(user, company, pricing_plan)
            
            # Create or get customer
            customer_result = self.create_customer(user, company)
            if not customer_result['success']:
                return customer_result
            
            customer_id = customer_result['customer_id']
            
            # Create Stripe price object for this plan
            price_result = self._get_or_create_stripe_price(pricing_plan)
            if not price_result['success']:
                return price_result
            
            price_id = price_result['price_id']
            
            # Get frontend URL from settings
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{frontend_url}/dashboard/subscriptions?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{frontend_url}/dashboard/subscriptions?canceled=true",
                metadata={
                    'user_id': user.id,
                    'company_id': company.id,
                    'plan_type': plan_type,
                    'pricing_plan_id': pricing_plan.id
                },
                subscription_data={
                    'metadata': {
                        'user_id': user.id,
                        'company_id': company.id,
                        'plan_type': plan_type,
                        'pricing_plan_id': pricing_plan.id
                    }
                }
            )
            
            return {
                'success': True,
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'message': 'Checkout session created successfully'
            }
            
        except stripe.StripeError as e:
            logger.error(f"Stripe error creating checkout for {user.email}: {str(e)}")
            return {
                'success': False,
                'message': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error creating checkout for {user.email}: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating checkout: {str(e)}'
            }
    
    def _create_free_subscription(self, user: User, company: Company, pricing_plan: PricingPlan) -> Dict[str, Any]:
        """
        Create a free subscription without Stripe payment
        """
        try:
            # Calculate subscription dates
            start_date = timezone.now().date()
            # Free plan is valid for 1 year by default
            end_date = start_date + relativedelta(years=1)
            
            # Create or update subscription
            subscription, created = Subscription.objects.update_or_create(
                company=company,
                defaults={
                    'plan': pricing_plan.plan_type,
                    'status': 'active',
                    'start_date': start_date,
                    'end_date': end_date,
                    'auto_renew': True,
                    'last_payment': start_date,
                    'amount': f'{pricing_plan.price} {pricing_plan.currency}',
                    'contact_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                    'contact_email': user.email
                }
            )
            
            return {
                'success': True,
                'subscription': subscription,
                'message': f'Free subscription {"created" if created else "updated"} successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating free subscription for {user.email}: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating subscription: {str(e)}'
            }
    
    def _get_or_create_stripe_price(self, pricing_plan: PricingPlan) -> Dict[str, Any]:
        """
        Get or create a Stripe price object for a pricing plan
        """
        try:
            # Create a unique lookup key for this plan
            lookup_key = f"plan_{pricing_plan.plan_type}_{int(pricing_plan.price * 100)}_{pricing_plan.currency.lower()}"
            
            # Try to find existing price
            prices = stripe.Price.list(
                lookup_keys=[lookup_key],
                limit=1
            )
            
            if prices.data:
                price = prices.data[0]
                logger.info(f"Found existing Stripe price {price.id} for plan {pricing_plan.plan_type}")
                return {
                    'success': True,
                    'price_id': price.id,
                    'price': price
                }
            
            # Create new price
            price = stripe.Price.create(
                unit_amount=int(pricing_plan.price * 100),  # Convert to cents
                currency=pricing_plan.currency.lower(),
                recurring={'interval': 'month'},
                product_data={
                    'name': pricing_plan.name,
                },
                lookup_key=lookup_key,
                metadata={
                    'plan_type': pricing_plan.plan_type,
                    'pricing_plan_id': pricing_plan.id
                }
            )
            
            logger.info(f"Created Stripe price {price.id} for plan {pricing_plan.plan_type}")
            return {
                'success': True,
                'price_id': price.id,
                'price': price
            }
            
        except stripe.StripeError as e:
            logger.error(f"Stripe error creating price for plan {pricing_plan.plan_type}: {str(e)}")
            return {
                'success': False,
                'message': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error creating price for plan {pricing_plan.plan_type}: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating price: {str(e)}'
            }
    
    def handle_subscription_created(self, stripe_subscription: stripe.Subscription) -> Dict[str, Any]:
        """
        Handle successful subscription creation from Stripe webhook
        """
        try:
            # Extract metadata
            metadata = stripe_subscription.metadata
            user_id = metadata.get('user_id')
            company_id = metadata.get('company_id')
            plan_type = metadata.get('plan_type')
            
            if not all([user_id, company_id, plan_type]):
                logger.error(f"Missing metadata in subscription {stripe_subscription.id}")
                return {
                    'success': False,
                    'message': 'Missing required metadata'
                }
            
            # Get user and company
            try:
                user = User.objects.get(id=user_id)
                company = Company.objects.get(id=company_id)
            except (User.DoesNotExist, Company.DoesNotExist) as e:
                logger.error(f"User or company not found: {str(e)}")
                return {
                    'success': False,
                    'message': 'User or company not found'
                }
            
            # Calculate subscription dates
            start_date = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_start
            ).date()
            end_date = timezone.datetime.fromtimestamp(
                stripe_subscription.current_period_end
            ).date()
            
            # Get amount from Stripe subscription
            amount_cents = stripe_subscription.items.data[0].price.unit_amount
            amount = Decimal(amount_cents) / 100
            currency = stripe_subscription.items.data[0].price.currency.upper()
            
            # Create or update subscription
            subscription, created = Subscription.objects.update_or_create(
                company=company,
                defaults={
                    'plan': plan_type,
                    'status': 'active',
                    'start_date': start_date,
                    'end_date': end_date,
                    'auto_renew': True,
                    'last_payment': start_date,
                    'amount': f'{amount} {currency}',
                    'contact_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                    'contact_email': user.email
                }
            )
            
            logger.info(f"Subscription {'created' if created else 'updated'} for company {company.official_name}")
            
            return {
                'success': True,
                'subscription': subscription,
                'message': f'Subscription {"created" if created else "updated"} successfully'
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription creation {stripe_subscription.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error handling subscription: {str(e)}'
            }
    
    def cancel_subscription(self, user: User, company: Company) -> Dict[str, Any]:
        """
        Cancel a user's subscription
        """
        try:
            # Get current subscription
            try:
                subscription = Subscription.objects.get(company=company)
            except Subscription.DoesNotExist:
                return {
                    'success': False,
                    'message': 'No active subscription found'
                }
            
            # If it's a free plan, just deactivate it
            if subscription.plan == 'free':
                subscription.status = 'expired'
                subscription.auto_renew = False
                subscription.save()
                
                return {
                    'success': True,
                    'message': 'Free subscription canceled'
                }
            
            # For paid plans, cancel the Stripe subscription
            # First, find the Stripe subscription
            customer_result = self.create_customer(user, company)
            if not customer_result['success']:
                return customer_result
            
            customer_id = customer_result['customer_id']
            
            # Find active subscriptions for this customer
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='active'
            )
            
            if not subscriptions.data:
                # Update local subscription status
                subscription.status = 'expired'
                subscription.auto_renew = False
                subscription.save()
                
                return {
                    'success': True,
                    'message': 'Subscription canceled (no active Stripe subscription found)'
                }
            
            # Cancel the Stripe subscription
            stripe_subscription = subscriptions.data[0]
            canceled_subscription = stripe.Subscription.delete(stripe_subscription.id)
            
            # Update local subscription
            subscription.status = 'expired'
            subscription.auto_renew = False
            subscription.save()
            
            return {
                'success': True,
                'message': 'Subscription canceled successfully'
            }
            
        except stripe.StripeError as e:
            logger.error(f"Stripe error canceling subscription for {user.email}: {str(e)}")
            return {
                'success': False,
                'message': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error canceling subscription for {user.email}: {str(e)}")
            return {
                'success': False,
                'message': f'Error canceling subscription: {str(e)}'
            }
    
    def get_subscription_status(self, user: User, company: Company) -> Dict[str, Any]:
        """
        Get the current subscription status from both local database and Stripe
        """
        try:
            # Get local subscription
            try:
                subscription = Subscription.objects.get(company=company)
            except Subscription.DoesNotExist:
                return {
                    'success': True,
                    'subscription': None,
                    'has_subscription': False,
                    'message': 'No subscription found'
                }
            
            # For free plans, return local data
            if subscription.plan == 'free':
                return {
                    'success': True,
                    'subscription': subscription,
                    'has_subscription': True,
                    'message': 'Free subscription active'
                }
            
            # For paid plans, check Stripe status
            customer_result = self.create_customer(user, company)
            if customer_result['success']:
                customer_id = customer_result['customer_id']
                
                # Get active Stripe subscriptions
                stripe_subscriptions = stripe.Subscription.list(
                    customer=customer_id,
                    status='active'
                )
                
                if stripe_subscriptions.data:
                    stripe_sub = stripe_subscriptions.data[0]
                    
                    # Update local subscription if needed
                    if subscription.status != 'active':
                        subscription.status = 'active'
                        subscription.save()
                
            return {
                'success': True,
                'subscription': subscription,
                'has_subscription': True,
                'message': 'Subscription found'
            }
            
        except Exception as e:
            logger.error(f"Error getting subscription status for {user.email}: {str(e)}")
            return {
                'success': False,
                'message': f'Error getting subscription status: {str(e)}'
            }
