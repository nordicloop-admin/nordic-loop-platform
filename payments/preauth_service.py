"""
Pre-Authorization Service for Bid Payments

This service handles the creation and management of payment authorization holds
when users place bids, ensuring funds are available before auction completion.
"""

import stripe
import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from bids.models import Bid
from users.models import User
from payments.models import StripeAccount
from payments.services import CommissionCalculatorService

logger = logging.getLogger(__name__)


class PreAuthorizationService:
    """
    Service for handling Stripe pre-authorization holds on bid placements
    """
    
    def __init__(self):
        self.stripe_api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        self.commission_service = CommissionCalculatorService()
        
        if not self.stripe_api_key:
            logger.warning("Stripe API key not configured")
        else:
            stripe.api_key = self.stripe_api_key
    
    def create_authorization_hold(self, bid: Bid, payment_method_id: str) -> Dict[str, Any]:
        """
        Create an authorization hold for a bid amount
        
        Args:
            bid: The bid object to authorize payment for
            payment_method_id: Stripe payment method ID from frontend
            
        Returns:
            Dict with success status and authorization details
        """
        try:
            # Validate seller has Stripe account through their company
            seller = bid.ad.user
            if not seller.company or not seller.company.stripe_account_id or not seller.company.payment_ready:
                return {
                    'success': False,
                    'message': 'Seller payment account not set up'
                }
            
            seller_company = seller.company
            
            # Calculate total amount for authorization
            total_amount = bid.bid_price_per_unit * bid.volume_requested
            total_amount_cents = int(total_amount * 100)
            
            # Get commission rate and calculate amounts
            commission_rate = self.commission_service.get_commission_rate(bid.user)
            commission_amount, seller_amount = self.commission_service.calculate_commission_amounts(
                total_amount, commission_rate
            )
            commission_amount_cents = int(commission_amount * 100)
            
            # Check if this is a test account
            is_test_account = seller_company.stripe_account_id.startswith('acct_test_')
            
            # Create payment intent with manual capture (authorization only)
            intent_params = {
                'amount': total_amount_cents,
                'currency': bid.ad.currency.lower(),
                'payment_method': payment_method_id,
                'capture_method': 'manual',  # This creates authorization hold
                'confirm': True,  # Confirm immediately with the provided payment method
                'automatic_payment_methods': {
                    'enabled': True,
                    'allow_redirects': 'never'  # Disable redirect-based payment methods
                },
                'metadata': {
                    'bid_id': bid.id,
                    'ad_id': bid.ad.id,
                    'buyer_id': bid.user.id,
                    'seller_id': seller.id,
                    'commission_rate': str(commission_rate),
                    'authorization_type': 'bid_preauth',
                },
            }
            
            # Add transfer data for non-test accounts
            if not is_test_account and seller_company.stripe_capabilities_complete:
                intent_params.update({
                    'application_fee_amount': commission_amount_cents,
                    'transfer_data': {
                        'destination': seller_company.stripe_account_id,
                    },
                })
            
            # Create the payment intent
            payment_intent = stripe.PaymentIntent.create(**intent_params)
            
            # Update bid with authorization details
            with transaction.atomic():
                bid.stripe_payment_method_id = payment_method_id
                bid.stripe_payment_intent_id = payment_intent.id
                # Map Stripe status to our model's status choices
                if payment_intent.status == 'requires_capture':
                    bid.authorization_status = 'authorized'
                elif payment_intent.status == 'succeeded':
                    bid.authorization_status = 'captured'
                else:
                    bid.authorization_status = 'pending'
                bid.authorization_amount = total_amount
                bid.authorization_created_at = timezone.now()
                # Authorization typically expires in 7 days
                bid.authorization_expires_at = timezone.now() + timedelta(days=7)
                bid.save()
            
            logger.info(f"Authorization hold created for bid {bid.id}: {payment_intent.id}")
            
            return {
                'success': True,
                'payment_intent_id': payment_intent.id,
                'status': payment_intent.status,
                'authorized_amount': total_amount,
                'commission_amount': commission_amount,
                'seller_amount': seller_amount,
                'expires_at': bid.authorization_expires_at,
                'message': 'Authorization hold created successfully'
            }
            
        except stripe.error.CardError as e:
            logger.error(f"Card error creating authorization for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Card declined: {e.user_message}',
                'error_code': e.code
            }
        except stripe.error.InvalidRequestError as e:
            logger.error(f"Invalid request error creating authorization for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Payment configuration error: {str(e)}'
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating authorization for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Payment error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error creating authorization for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing payment authorization: {str(e)}'
            }
    
    def capture_authorization(self, bid: Bid) -> Dict[str, Any]:
        """
        Capture (charge) an authorized payment when bid wins
        
        Args:
            bid: The winning bid to capture payment for
            
        Returns:
            Dict with success status and capture details
        """
        try:
            if not bid.stripe_payment_intent_id:
                return {
                    'success': False,
                    'message': 'No authorization found for this bid'
                }
            
            if bid.authorization_status != 'authorized':
                return {
                    'success': False,
                    'message': f'Authorization not ready for capture (status: {bid.authorization_status})'
                }
            
            # Capture the payment
            payment_intent = stripe.PaymentIntent.capture(bid.stripe_payment_intent_id)
            
            # Update bid status and create payment records
            with transaction.atomic():
                bid.authorization_status = 'captured'
                bid.status = 'paid'  # Mark bid as paid since money is captured
                bid.save()
                
                # Create PaymentIntent record if it doesn't exist
                from .models import PaymentIntent, Transaction
                from decimal import Decimal
                
                payment_intent_record, created = PaymentIntent.objects.get_or_create(
                    stripe_payment_intent_id=payment_intent.id,
                    defaults={
                        'bid': bid,
                        'buyer': bid.user,
                        'seller': bid.ad.user,
                        'total_amount': bid.authorization_amount,
                        'commission_amount': Decimal('0.00'),  # We can calculate this later
                        'seller_amount': bid.authorization_amount,  # We can calculate this later
                        'commission_rate': Decimal('5.00'),  # Default platform commission
                        'status': 'succeeded',
                        'currency': bid.ad.currency,
                        'confirmed_at': timezone.now()
                    }
                )
                
                # Calculate commission and seller amounts
                commission_rate = Decimal('5.00')  # 5% commission
                commission_amount = (bid.authorization_amount * commission_rate / Decimal('100')).quantize(Decimal('0.01'))
                seller_amount = bid.authorization_amount - commission_amount
                
                # Update payment intent record with correct amounts
                payment_intent_record.commission_amount = commission_amount
                payment_intent_record.seller_amount = seller_amount
                payment_intent_record.commission_rate = commission_rate
                payment_intent_record.save()
                
                # Create Transaction record for the payment (buyer -> platform)
                Transaction.objects.create(
                    payment_intent=payment_intent_record,
                    transaction_type='payment',
                    amount=bid.authorization_amount,
                    currency=bid.ad.currency,
                    status='completed',
                    from_user=bid.user,  # Buyer
                    to_user=None,  # Platform receives the payment first
                    stripe_charge_id=payment_intent.id,
                    description=f'Payment for auction: {bid.ad.title}',
                    metadata={
                        'bid_id': bid.id,
                        'auction_id': bid.ad.id,
                        'payment_type': 'bid_payment'
                    },
                    processed_at=timezone.now()
                )
                
                # Create pending payout transaction for the seller (platform -> seller)
                Transaction.objects.create(
                    payment_intent=payment_intent_record,
                    transaction_type='payout',
                    amount=seller_amount,
                    currency=bid.ad.currency,
                    status='pending',
                    from_user=None,  # Platform
                    to_user=bid.ad.user,  # Seller
                    description=f'Payout for auction: {bid.ad.title}',
                    metadata={
                        'bid_id': bid.id,
                        'auction_id': bid.ad.id,
                        'payment_type': 'seller_payout',
                        'commission_amount': str(commission_amount),
                        'original_payment_amount': str(bid.authorization_amount)
                    },
                    processed_at=None  # Will be set when payout is processed
                )
            
            logger.info(f"Authorization captured for winning bid {bid.id}: {payment_intent.id}")
            
            return {
                'success': True,
                'payment_intent_id': payment_intent.id,
                'status': payment_intent.status,
                'captured_amount': bid.authorization_amount,
                'message': 'Payment captured successfully'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error capturing authorization for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error capturing payment: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error capturing authorization for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing payment capture: {str(e)}'
            }
    
    def cancel_authorization(self, bid: Bid) -> Dict[str, Any]:
        """
        Cancel (release) an authorization hold when bid loses or is canceled
        
        Args:
            bid: The bid to release authorization for
            
        Returns:
            Dict with success status and cancellation details
        """
        try:
            if not bid.stripe_payment_intent_id:
                return {
                    'success': True,
                    'message': 'No authorization to cancel'
                }
            
            if bid.authorization_status in ['captured', 'canceled']:
                return {
                    'success': True,
                    'message': f'Authorization already {bid.authorization_status}'
                }
            
            # Cancel the payment intent
            payment_intent = stripe.PaymentIntent.cancel(bid.stripe_payment_intent_id)
            
            # Update bid status
            with transaction.atomic():
                bid.authorization_status = 'canceled'
                bid.save()
            
            logger.info(f"Authorization canceled for bid {bid.id}: {payment_intent.id}")
            
            return {
                'success': True,
                'payment_intent_id': payment_intent.id,
                'status': payment_intent.status,
                'released_amount': bid.authorization_amount,
                'message': 'Authorization released successfully'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling authorization for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error canceling authorization: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error canceling authorization for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing authorization cancellation: {str(e)}'
            }
    
    def check_authorization_expiry(self, bid: Bid) -> Dict[str, Any]:
        """
        Check if authorization is expiring soon and handle renewal if needed
        
        Args:
            bid: The bid to check authorization for
            
        Returns:
            Dict with authorization status and expiry info
        """
        try:
            if not bid.authorization_expires_at:
                return {
                    'success': False,
                    'message': 'No authorization expiry date set'
                }
            
            now = timezone.now()
            expires_at = bid.authorization_expires_at
            time_until_expiry = expires_at - now
            
            # Check if authorization expires within 24 hours
            if time_until_expiry.total_seconds() < 86400:  # 24 hours
                return {
                    'success': False,
                    'expired': time_until_expiry.total_seconds() <= 0,
                    'expires_soon': True,
                    'time_until_expiry': str(time_until_expiry),
                    'message': 'Authorization expires soon or has expired'
                }
            
            return {
                'success': True,
                'expired': False,
                'expires_soon': False,
                'time_until_expiry': str(time_until_expiry),
                'message': 'Authorization is valid'
            }
            
        except Exception as e:
            logger.error(f"Error checking authorization expiry for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error checking authorization expiry: {str(e)}'
            }
    
    def refresh_authorization(self, bid: Bid) -> Dict[str, Any]:
        """
        Create a new authorization if the current one is expiring
        
        Args:
            bid: The bid to refresh authorization for
            
        Returns:
            Dict with success status and new authorization details
        """
        try:
            if not bid.stripe_payment_method_id:
                return {
                    'success': False,
                    'message': 'No payment method stored for this bid'
                }
            
            # Cancel existing authorization if it exists
            if bid.stripe_payment_intent_id:
                self.cancel_authorization(bid)
            
            # Create new authorization
            return self.create_authorization_hold(bid, bid.stripe_payment_method_id)
            
        except Exception as e:
            logger.error(f"Error refreshing authorization for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error refreshing authorization: {str(e)}'
            }
    
    def get_authorization_status(self, bid: Bid) -> Dict[str, Any]:
        """
        Get current authorization status from Stripe
        
        Args:
            bid: The bid to check authorization status for
            
        Returns:
            Dict with current authorization status
        """
        try:
            if not bid.stripe_payment_intent_id:
                return {
                    'success': False,
                    'message': 'No authorization found'
                }
            
            # Retrieve payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(bid.stripe_payment_intent_id)
            
            # Update local status if different
            if bid.authorization_status != payment_intent.status:
                bid.authorization_status = payment_intent.status
                bid.save()
            
            return {
                'success': True,
                'payment_intent_id': payment_intent.id,
                'status': payment_intent.status,
                'amount': payment_intent.amount / 100,  # Convert from cents
                'currency': payment_intent.currency.upper(),
                'created': datetime.fromtimestamp(payment_intent.created),
                'message': 'Authorization status retrieved'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving authorization status for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error retrieving authorization status: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error retrieving authorization status for bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error checking authorization status: {str(e)}'
            }
