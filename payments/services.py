import stripe
import logging
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from users.models import User
from ads.models import Subscription
from .models import StripeAccount, PaymentIntent, Transaction, PayoutSchedule

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe_secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
if stripe_secret_key:
    stripe.api_key = stripe_secret_key
    logger.info("Stripe API key configured successfully")
else:
    logger.warning("Stripe API key not found in settings")


class StripeConnectService:
    """
    Service class for handling Stripe Connect operations
    """
    
    def __init__(self):
        self.stripe_api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not self.stripe_api_key:
            logger.warning("Stripe API key not configured")
        else:
            # Ensure stripe module uses the API key
            stripe.api_key = self.stripe_api_key
    
    def create_connect_account(self, user: User, bank_account_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Stripe Connect Custom account for a seller
        """
        try:
            # Ensure API key is set
            if not self.stripe_api_key:
                return {
                    'success': False,
                    'message': 'Stripe API key not configured'
                }
            # Create Stripe Custom account
            account = stripe.Account.create(
                type='custom',
                country=bank_account_data.get('bank_country', 'SE'),
                email=user.email,
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
                business_type='individual',
                individual={
                    'email': user.email,
                    'first_name': user.first_name or 'Unknown',
                    'last_name': user.last_name or 'User',
                },
                business_profile={
                    'mcc': '5999',  # Miscellaneous retail stores
                    'url': getattr(settings, 'FRONTEND_URL', 'https://nordicloop.se'),
                },
                tos_acceptance={
                    'date': int(timezone.now().timestamp()),
                    'ip': '127.0.0.1',  # You should pass the actual IP
                },
            )
            
            # Add bank account
            bank_account = stripe.Account.create_external_account(
                account.id,
                external_account={
                    'object': 'bank_account',
                    'country': bank_account_data.get('bank_country', 'SE'),
                    'currency': bank_account_data.get('currency', 'sek').lower(),
                    'account_holder_name': bank_account_data['account_holder_name'],
                    'account_number': bank_account_data['account_number'],
                    'routing_number': bank_account_data.get('routing_number', ''),
                }
            )
            
            # Create or update StripeAccount record
            stripe_account, created = StripeAccount.objects.update_or_create(
                user=user,
                defaults={
                    'stripe_account_id': account.id,
                    'account_status': 'pending',
                    'bank_account_last4': bank_account.last4,
                    'bank_name': bank_account_data.get('bank_name', ''),
                    'bank_country': bank_account_data.get('bank_country', 'SE'),
                    'charges_enabled': account.charges_enabled,
                    'payouts_enabled': account.payouts_enabled,
                }
            )
            
            return {
                'success': True,
                'account_id': account.id,
                'stripe_account': stripe_account,
                'message': 'Stripe account created successfully'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating account for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Stripe error: {str(e)}'
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating account for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error creating Stripe account for user {user.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }
    
    def update_account_status(self, stripe_account_id: str) -> Dict[str, Any]:
        """
        Update account status from Stripe
        """
        try:
            account = stripe.Account.retrieve(stripe_account_id)
            
            stripe_account = StripeAccount.objects.get(stripe_account_id=stripe_account_id)
            stripe_account.charges_enabled = account.charges_enabled
            stripe_account.payouts_enabled = account.payouts_enabled
            
            # Determine account status
            if account.charges_enabled and account.payouts_enabled:
                stripe_account.account_status = 'active'
            elif account.requirements.currently_due:
                stripe_account.account_status = 'restricted'
            else:
                stripe_account.account_status = 'pending'
            
            stripe_account.save()
            
            return {
                'success': True,
                'account_status': stripe_account.account_status,
                'charges_enabled': account.charges_enabled,
                'payouts_enabled': account.payouts_enabled
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating account {stripe_account_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Stripe error: {str(e)}'
            }
        except StripeAccount.DoesNotExist:
            return {
                'success': False,
                'message': 'Stripe account not found'
            }
        except Exception as e:
            logger.error(f"Error updating account status {stripe_account_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error updating account: {str(e)}'
            }
    
    def create_payment_intent(self, payment_intent_obj: PaymentIntent) -> Dict[str, Any]:
        """
        Create a Stripe Payment Intent for a bid payment
        """
        try:
            # Get seller's Stripe account
            seller_stripe_account = StripeAccount.objects.get(user=payment_intent_obj.seller)
            
            # Calculate amounts in cents (Stripe uses smallest currency unit)
            total_amount_cents = int(payment_intent_obj.total_amount * 100)
            commission_amount_cents = int(payment_intent_obj.commission_amount * 100)
            
            # Create Payment Intent with application fee
            intent = stripe.PaymentIntent.create(
                amount=total_amount_cents,
                currency=payment_intent_obj.currency.lower(),
                application_fee_amount=commission_amount_cents,
                transfer_data={
                    'destination': seller_stripe_account.stripe_account_id,
                },
                metadata={
                    'bid_id': payment_intent_obj.bid.id,
                    'buyer_id': payment_intent_obj.buyer.id,
                    'seller_id': payment_intent_obj.seller.id,
                    'commission_rate': str(payment_intent_obj.commission_rate),
                },
                automatic_payment_methods={
                    'enabled': True,
                },
            )
            
            # Update payment intent with Stripe ID
            payment_intent_obj.stripe_payment_intent_id = intent.id
            payment_intent_obj.status = intent.status
            payment_intent_obj.save()
            
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'message': 'Payment intent created successfully'
            }
            
        except StripeAccount.DoesNotExist:
            logger.error(f"Stripe account not found for seller {payment_intent_obj.seller.id}")
            return {
                'success': False,
                'message': 'Seller payment account not set up'
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            return {
                'success': False,
                'message': f'Payment error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating payment: {str(e)}'
            }
    
    def process_payout(self, payout_schedule: PayoutSchedule) -> Dict[str, Any]:
        """
        Process a payout to a seller
        """
        try:
            # Get seller's Stripe account
            seller_stripe_account = StripeAccount.objects.get(user=payout_schedule.seller)
            
            if not seller_stripe_account.payouts_enabled:
                return {
                    'success': False,
                    'message': 'Seller account not enabled for payouts'
                }
            
            # Calculate payout amount in cents
            payout_amount_cents = int(payout_schedule.total_amount * 100)
            
            # Create payout
            payout = stripe.Payout.create(
                amount=payout_amount_cents,
                currency=payout_schedule.currency.lower(),
                stripe_account=seller_stripe_account.stripe_account_id,
                metadata={
                    'payout_schedule_id': str(payout_schedule.id),
                    'seller_id': payout_schedule.seller.id,
                }
            )
            
            # Update payout schedule
            payout_schedule.stripe_payout_id = payout.id
            payout_schedule.status = 'processing'
            payout_schedule.processed_date = timezone.now().date()
            payout_schedule.save()
            
            # Update related transactions
            payout_schedule.transactions.filter(status='pending').update(
                status='completed',
                processed_at=timezone.now()
            )
            
            return {
                'success': True,
                'payout_id': payout.id,
                'message': 'Payout processed successfully'
            }
            
        except StripeAccount.DoesNotExist:
            logger.error(f"Stripe account not found for seller {payout_schedule.seller.id}")
            return {
                'success': False,
                'message': 'Seller payment account not found'
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing payout: {str(e)}")
            return {
                'success': False,
                'message': f'Payout error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error processing payout: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing payout: {str(e)}'
            }


class CommissionCalculatorService:
    """
    Service for calculating commission rates based on subscription plans
    """
    
    COMMISSION_RATES = {
        'free': Decimal('9.00'),      # 9%
        'standard': Decimal('7.00'),  # 7%
        'premium': Decimal('0.00'),   # 0%
    }
    
    def get_commission_rate(self, user: User) -> Decimal:
        """
        Get commission rate for a user based on their subscription plan
        """
        try:
            # Get user's active subscription
            subscription = Subscription.objects.filter(
                company=user.company,
                status='active'
            ).first()
            
            if subscription:
                return self.COMMISSION_RATES.get(subscription.plan, self.COMMISSION_RATES['free'])
            else:
                # Default to free plan commission
                return self.COMMISSION_RATES['free']
                
        except Exception as e:
            logger.error(f"Error getting commission rate for user {user.id}: {str(e)}")
            return self.COMMISSION_RATES['free']
    
    def calculate_commission_amounts(self, total_amount: Decimal, commission_rate: Decimal) -> Tuple[Decimal, Decimal]:
        """
        Calculate commission and seller amounts
        """
        commission_amount = (total_amount * commission_rate / 100).quantize(Decimal('0.01'))
        seller_amount = total_amount - commission_amount
        
        return commission_amount, seller_amount
