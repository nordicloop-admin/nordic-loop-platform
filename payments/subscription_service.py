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

# Constants
STRIPE_API_KEY_NOT_CONFIGURED = 'Stripe API key not configured'


class StripeSubscriptionService:
    """
    Service for handling Stripe subscription payments
    """
    
    def __init__(self):
        self.stripe_api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not self.stripe_api_key:
            logger.warning(STRIPE_API_KEY_NOT_CONFIGURED)
        else:
            stripe.api_key = self.stripe_api_key
    
    def create_customer(self, user: User, company: Company) -> Dict[str, Any]:
        """
        Create or get existing Stripe customer for a user/company
        """
        try:
            if not self.stripe_api_key:
                return {
                    'success': False,
                    'message': STRIPE_API_KEY_NOT_CONFIGURED
                }
            
            # First check if we already have a stored customer ID
            try:
                subscription = Subscription.objects.get(company=company)
                if subscription.stripe_customer_id:
                    try:
                        # Verify customer still exists in Stripe
                        customer = stripe.Customer.retrieve(subscription.stripe_customer_id)
                        if customer.deleted:
                            # Customer was deleted, create new one
                            logger.info(f"Stored customer {subscription.stripe_customer_id} was deleted, creating new one")
                        else:
                            logger.info(f"Found stored Stripe customer {customer.id} for {user.email}")
                            return {
                                'success': True,
                                'customer_id': customer.id,
                                'customer': customer,
                                'message': 'Found stored customer'
                            }
                    except stripe.InvalidRequestError:
                        # Customer ID is invalid, we'll create a new one
                        logger.warning(f"Invalid stored customer ID {subscription.stripe_customer_id} for {user.email}")
            except Subscription.DoesNotExist:
                pass
            
            # Check if customer already exists by email (fallback)
            existing_customers = stripe.Customer.list(
                email=user.email,
                limit=1
            )
            
            if existing_customers.data:
                customer = existing_customers.data[0]
                logger.info(f"Found existing Stripe customer {customer.id} for {user.email}")
                
                # Store the customer ID in our subscription if we have one
                try:
                    subscription = Subscription.objects.get(company=company)
                    subscription.stripe_customer_id = customer.id
                    subscription.save()
                    logger.info(f"Updated local subscription with customer ID {customer.id}")
                except Subscription.DoesNotExist:
                    pass
                
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
                    'user_id': str(user.id),
                    'company_id': str(company.id),
                    'company_name': company.official_name,
                    'user_email': user.email
                }
            )
            
            # Store customer ID in subscription if exists
            try:
                subscription = Subscription.objects.get(company=company)
                subscription.stripe_customer_id = customer.id
                subscription.save()
                logger.info(f"Updated local subscription with new customer ID {customer.id}")
            except Subscription.DoesNotExist:
                pass
            
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
                    'message': STRIPE_API_KEY_NOT_CONFIGURED
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
            
            # Check if user already has an active subscription for this company
            existing_subscription = None
            try:
                existing_subscription = Subscription.objects.get(company=company)
                if existing_subscription.is_paid_plan() and existing_subscription.stripe_subscription_id:
                    # Cancel existing Stripe subscription before creating new one
                    try:
                        stripe.Subscription.delete(existing_subscription.stripe_subscription_id)
                        logger.info(f"Canceled existing subscription {existing_subscription.stripe_subscription_id}")
                    except stripe.InvalidRequestError as e:
                        logger.warning(f"Could not cancel existing subscription: {str(e)}")
            except Subscription.DoesNotExist:
                pass
            
            # Create checkout session with enhanced metadata
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
                    'user_id': str(user.id),
                    'company_id': str(company.id),
                    'plan_type': plan_type,
                    'pricing_plan_id': str(pricing_plan.id),
                    'user_email': user.email,
                    'company_name': company.official_name
                },
                subscription_data={
                    'metadata': {
                        'user_id': str(user.id),
                        'company_id': str(company.id),
                        'plan_type': plan_type,
                        'pricing_plan_id': str(pricing_plan.id),
                        'user_email': user.email,
                        'company_name': company.official_name
                    }
                },
                # Enable customer to manage their subscription
                allow_promotion_codes=True,
                billing_address_collection='auto',
                customer_update={
                    'address': 'auto',
                    'name': 'auto'
                }
            )
            
            logger.info(f"Created checkout session {checkout_session.id} for {user.email} - {plan_type} plan")
            
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
            
            # Get or create customer to maintain consistency
            customer_result = self.create_customer(user, company)
            customer_id = None
            if customer_result['success']:
                customer_id = customer_result['customer_id']
            
            # Create or update subscription
            subscription, created = Subscription.objects.update_or_create(
                company=company,
                defaults={
                    'plan': pricing_plan.plan_type,
                    'status': 'active',
                    'start_date': start_date,
                    'end_date': end_date,
                    'next_billing_date': None,  # Free plans don't have billing dates
                    'auto_renew': True,
                    'last_payment': start_date,
                    'amount': f'{pricing_plan.price} {pricing_plan.currency}',
                    'contact_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                    'contact_email': user.email,
                    'stripe_customer_id': customer_id,
                    'stripe_subscription_id': None,  # Free plans don't have Stripe subscriptions
                    'stripe_price_id': None,
                    'cancel_at_period_end': False,
                    'trial_end': None
                }
            )
            
            action = "created" if created else "updated"
            logger.info(f"Free subscription {action} for company {company.official_name}")
            
            return {
                'success': True,
                'subscription': subscription,
                'is_free_plan': True,
                'message': f'Free subscription {action} successfully'
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
                logger.error(f"Missing metadata in subscription {stripe_subscription.id}: {metadata}")
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
            next_billing_date = end_date
            
            # Get amount and currency from Stripe subscription
            if stripe_subscription.items.data:
                price = stripe_subscription.items.data[0].price
                amount_cents = price.unit_amount
                amount = Decimal(amount_cents) / 100 if amount_cents else Decimal('0')
                currency = price.currency.upper()
                stripe_price_id = price.id
            else:
                amount = Decimal('0')
                currency = 'SEK'
                stripe_price_id = None
            
            # Map Stripe subscription status to our status
            status_mapping = {
                'active': 'active',
                'trialing': 'trialing',
                'past_due': 'past_due',
                'canceled': 'canceled',
                'unpaid': 'unpaid',
                'incomplete': 'incomplete',
                'incomplete_expired': 'expired',
            }
            local_status = status_mapping.get(stripe_subscription.status, 'active')
            
            # Create or update subscription with Stripe IDs
            subscription, created = Subscription.objects.update_or_create(
                company=company,
                defaults={
                    'plan': plan_type,
                    'status': local_status,
                    'start_date': start_date,
                    'end_date': end_date,
                    'next_billing_date': next_billing_date,
                    'auto_renew': not stripe_subscription.cancel_at_period_end,
                    'last_payment': start_date if local_status == 'active' else None,
                    'amount': f'{amount} {currency}',
                    'contact_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                    'contact_email': user.email,
                    # Store Stripe IDs for proper tracking
                    'stripe_customer_id': stripe_subscription.customer,
                    'stripe_subscription_id': stripe_subscription.id,
                    'stripe_price_id': stripe_price_id,
                    'cancel_at_period_end': stripe_subscription.cancel_at_period_end,
                    'trial_end': timezone.datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None
                }
            )
            
            action = "created" if created else "updated"
            logger.info(f"Subscription {action} for company {company.official_name}: {stripe_subscription.id}")
            
            return {
                'success': True,
                'subscription': subscription,
                'created': created,
                'message': f'Subscription {action} successfully'
            }
            
        except Exception as e:
            logger.error(f"Error handling subscription creation {stripe_subscription.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error handling subscription: {str(e)}'
            }
    
    def change_subscription_plan(self, user: User, company: Company, new_plan_type: str) -> Dict[str, Any]:
        """
        Change user's subscription plan (upgrade/downgrade)
        """
        try:
            if not self.stripe_api_key:
                return {
                    'success': False,
                    'message': STRIPE_API_KEY_NOT_CONFIGURED
                }
            
            # Get new pricing plan
            try:
                new_pricing_plan = PricingPlan.objects.get(plan_type=new_plan_type, is_active=True)
            except PricingPlan.DoesNotExist:
                return {
                    'success': False,
                    'message': f'Pricing plan "{new_plan_type}" not found'
                }
            
            # Get current subscription
            try:
                current_subscription = Subscription.objects.get(company=company)
            except Subscription.DoesNotExist:
                # No current subscription, create new one
                return self.create_subscription_checkout(user, company, new_plan_type)
            
            # If changing to the same plan, do nothing
            if current_subscription.plan == new_plan_type:
                return {
                    'success': True,
                    'message': f'Already subscribed to {new_plan_type} plan'
                }
            
            # Handle change to free plan
            if new_plan_type == 'free':
                return self._downgrade_to_free(current_subscription, new_pricing_plan)
            
            # Handle change from free plan to paid plan
            if current_subscription.plan == 'free':
                return self.create_subscription_checkout(user, company, new_plan_type)
            
            # Handle paid plan to paid plan change
            if current_subscription.stripe_subscription_id:
                return self._modify_stripe_subscription(current_subscription, new_pricing_plan, new_plan_type)
            else:
                # Subscription exists but no Stripe subscription ID, create new checkout
                return self.create_subscription_checkout(user, company, new_plan_type)
                
        except Exception as e:
            logger.error(f"Error changing subscription plan for {user.email}: {str(e)}")
            return {
                'success': False,
                'message': f'Error changing subscription plan: {str(e)}'
            }
    
    def _downgrade_to_free(self, current_subscription: Subscription, new_pricing_plan: PricingPlan) -> Dict[str, Any]:
        """
        Downgrade current paid subscription to free plan
        """
        try:
            # Cancel Stripe subscription if it exists
            if current_subscription.stripe_subscription_id:
                try:
                    stripe.Subscription.modify(
                        current_subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                    logger.info(f"Set Stripe subscription to cancel at period end: {current_subscription.stripe_subscription_id}")
                except stripe.StripeError as e:
                    logger.error(f"Error canceling Stripe subscription: {str(e)}")
                    # Continue with local update even if Stripe fails
            
            # Update local subscription
            current_subscription.plan = new_pricing_plan.plan_type
            current_subscription.status = 'active'
            current_subscription.cancel_at_period_end = True
            current_subscription.auto_renew = False
            current_subscription.amount = f'{new_pricing_plan.price} {new_pricing_plan.currency}'
            current_subscription.save()
            
            return {
                'success': True,
                'is_free_plan': True,
                'message': 'Subscription will be downgraded to free plan at the end of current billing period'
            }
            
        except Exception as e:
            logger.error(f"Error downgrading to free plan: {str(e)}")
            return {
                'success': False,
                'message': f'Error downgrading to free plan: {str(e)}'
            }
    
    def _modify_stripe_subscription(self, current_subscription: Subscription, new_pricing_plan: PricingPlan, new_plan_type: str) -> Dict[str, Any]:
        """
        Modify existing Stripe subscription to change plan
        """
        try:
            # Get or create new price
            price_result = self._get_or_create_stripe_price(new_pricing_plan)
            if not price_result['success']:
                return price_result
            
            new_price_id = price_result['price_id']
            
            # Get current Stripe subscription
            stripe_subscription = stripe.Subscription.retrieve(current_subscription.stripe_subscription_id)
            
            # Update the subscription with new price
            updated_subscription = stripe.Subscription.modify(
                current_subscription.stripe_subscription_id,
                items=[{
                    'id': stripe_subscription['items']['data'][0]['id'],
                    'price': new_price_id,
                }],
                metadata={
                    'user_id': str(current_subscription.company.user.id),
                    'company_id': str(current_subscription.company.id),
                    'plan_type': new_plan_type,
                    'pricing_plan_id': str(new_pricing_plan.id),
                    'user_email': current_subscription.contact_email,
                    'company_name': current_subscription.company.official_name
                },
                proration_behavior='create_prorations'  # Prorate the change
            )
            
            # Update local subscription
            amount_cents = updated_subscription.items.data[0].price.unit_amount
            amount = Decimal(amount_cents) / 100 if amount_cents else Decimal('0')
            currency = updated_subscription.items.data[0].price.currency.upper()
            
            current_subscription.plan = new_plan_type
            current_subscription.amount = f'{amount} {currency}'
            current_subscription.stripe_price_id = new_price_id
            current_subscription.save()
            
            logger.info(f"Modified Stripe subscription {current_subscription.stripe_subscription_id} to {new_plan_type} plan")
            
            return {
                'success': True,
                'message': f'Subscription changed to {new_plan_type} plan successfully',
                'prorated': True
            }
            
        except stripe.StripeError as e:
            logger.error(f"Stripe error modifying subscription: {str(e)}")
            return {
                'success': False,
                'message': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error modifying subscription: {str(e)}")
            return {
                'success': False,
                'message': f'Error modifying subscription: {str(e)}'
            }
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
            stripe.Subscription.delete(stripe_subscription.id)
            
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
