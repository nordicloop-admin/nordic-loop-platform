import logging
from decimal import Decimal
from typing import Dict, Any, List
from django.utils import timezone
from django.db import transaction
from bids.models import Bid
from users.models import User
from .models import PaymentIntent, Transaction, PayoutSchedule, StripeAccount
from .services import StripeConnectService, CommissionCalculatorService
from .completion_services.payment_completion import PaymentCompletionService

logger = logging.getLogger(__name__)


class BidPaymentProcessor:
    """
    Processor for handling bid payments when bids are won
    """
    
    def __init__(self):
        self.stripe_service = StripeConnectService()
        self.commission_service = CommissionCalculatorService()
        self.completion_service = PaymentCompletionService()
    
    def process_winning_bid(self, bid: Bid) -> Dict[str, Any]:
        """
        Process payment for a winning bid
        """
        try:
            if bid.status != 'won':
                return {
                    'success': False,
                    'message': 'Bid is not in won status'
                }
            
            # Check if payment intent already exists
            if hasattr(bid, 'payment_intent'):
                existing_payment_intent = bid.payment_intent
                
                # If payment intent exists and has a Stripe ID, retrieve the client secret
                if existing_payment_intent.stripe_payment_intent_id:
                    try:
                        import stripe
                        stripe.api_key = self.stripe_service.stripe_api_key
                        
                        # Retrieve existing Stripe payment intent
                        stripe_intent = stripe.PaymentIntent.retrieve(existing_payment_intent.stripe_payment_intent_id)
                        
                        # Update local status if needed
                        if existing_payment_intent.status != stripe_intent.status:
                            existing_payment_intent.status = stripe_intent.status
                            existing_payment_intent.save()
                        
                        return {
                            'success': True,
                            'payment_intent': existing_payment_intent,
                            'client_secret': stripe_intent.client_secret,
                            'message': 'Using existing payment intent'
                        }
                    except Exception as e:
                        logger.error(f"Error retrieving existing Stripe intent {existing_payment_intent.stripe_payment_intent_id}: {str(e)}")
                        # If we can't retrieve it, we'll create a new one by continuing the flow
                        logger.info(f"Creating new payment intent to replace failed one for bid {bid.id}")
                else:
                    # Payment intent exists but no Stripe ID - create Stripe intent
                    try:
                        stripe_result = self.stripe_service.create_payment_intent(existing_payment_intent)
                        if stripe_result['success']:
                            return {
                                'success': True,
                                'payment_intent': existing_payment_intent,
                                'client_secret': stripe_result['client_secret'],
                                'message': 'Stripe intent created for existing payment intent'
                            }
                        else:
                            logger.error(f"Failed to create Stripe intent for existing payment intent {existing_payment_intent.id}")
                            return {
                                'success': False,
                                'message': 'Failed to initialize existing payment intent'
                            }
                    except Exception as e:
                        logger.error(f"Error creating Stripe intent for existing payment intent {existing_payment_intent.id}: {str(e)}")
                        return {
                            'success': False,
                            'message': 'Error with existing payment intent'
                        }
            
            # Get buyer and seller
            buyer = bid.user
            seller = bid.ad.user
            
            if not seller:
                return {
                    'success': False,
                    'message': 'Seller not found for this ad'
                }
            
            # Check if seller has Stripe account
            if not hasattr(seller, 'stripe_account'):
                return {
                    'success': False,
                    'message': 'Seller has not set up payment account'
                }
            
            # Calculate total amount
            total_amount = bid.bid_price_per_unit * bid.volume_requested
            
            # Get commission rate for buyer
            commission_rate = self.commission_service.get_commission_rate(buyer)
            
            # Calculate commission and seller amounts
            commission_amount, seller_amount = self.commission_service.calculate_commission_amounts(
                total_amount, commission_rate
            )
            
            # Create payment intent record
            with transaction.atomic():
                payment_intent = PaymentIntent.objects.create(
                    bid=bid,
                    buyer=buyer,
                    seller=seller,
                    total_amount=total_amount,
                    commission_amount=commission_amount,
                    seller_amount=seller_amount,
                    commission_rate=commission_rate,
                    currency='SEK'
                )
                
                # Create Stripe payment intent
                stripe_result = self.stripe_service.create_payment_intent(payment_intent)
                
                if not stripe_result['success']:
                    # Delete the payment intent if Stripe creation failed
                    payment_intent.delete()
                    return stripe_result
                
                return {
                    'success': True,
                    'payment_intent': payment_intent,
                    'client_secret': stripe_result['client_secret'],
                    'message': 'Payment intent created successfully'
                }
                
        except Exception as e:
            logger.error(f"Error processing winning bid {bid.id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing payment: {str(e)}'
            }
    
    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Confirm a payment intent (called by webhook) and process completion
        """
        try:
            payment_intent = PaymentIntent.objects.get(stripe_payment_intent_id=payment_intent_id)

            # Update status
            payment_intent.status = 'succeeded'
            payment_intent.confirmed_at = timezone.now()
            payment_intent.save()

            # Process payment completion (status updates, notifications)
            completion_result = self.completion_service.process_payment_completion(payment_intent)

            return {
                'success': True,
                'payment_intent': payment_intent,
                'message': 'Payment confirmed successfully',
                'completion_result': completion_result
            }

        except PaymentIntent.DoesNotExist:
            logger.error(f"Payment intent not found: {payment_intent_id}")
            return {
                'success': False,
                'message': 'Payment intent not found'
            }
        except Exception as e:
            logger.error(f"Error confirming payment {payment_intent_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error confirming payment: {str(e)}'
            }

    def handle_payment_failure(self, payment_intent_id: str, failure_reason: str) -> Dict[str, Any]:
        """
        Handle payment failure (called by webhook)
        """
        try:
            payment_intent = PaymentIntent.objects.get(stripe_payment_intent_id=payment_intent_id)

            # Update status
            payment_intent.status = 'requires_payment_method'
            payment_intent.save()

            # Process payment failure (notifications)
            failure_result = self.completion_service.handle_payment_failure(payment_intent, failure_reason)

            return {
                'success': True,
                'payment_intent': payment_intent,
                'message': 'Payment failure handled',
                'failure_result': failure_result
            }

        except PaymentIntent.DoesNotExist:
            logger.error(f"Payment intent not found: {payment_intent_id}")
            return {
                'success': False,
                'message': 'Payment intent not found'
            }
        except Exception as e:
            logger.error(f"Error handling payment failure {payment_intent_id}: {str(e)}")
            return {
                'success': False,
                'message': f'Error handling payment failure: {str(e)}'
            }


class PayoutProcessor:
    """
    Processor for handling seller payouts
    """
    
    def __init__(self):
        self.stripe_service = StripeConnectService()
    
    def create_payout_schedule(self, seller_ids: List[int], scheduled_date, created_by: User, notes: str = '') -> Dict[str, Any]:
        """
        Create payout schedules for multiple sellers
        """
        try:
            created_schedules = []
            errors = []
            
            for seller_id in seller_ids:
                try:
                    seller = User.objects.get(id=seller_id)
                    
                    # Calculate pending payout amount
                    pending_transactions = Transaction.objects.filter(
                        to_user=seller,
                        transaction_type='payout',
                        status='pending'
                    )
                    
                    if not pending_transactions.exists():
                        errors.append(f"No pending payouts for seller {seller.email}")
                        continue
                    
                    total_amount = sum(t.amount for t in pending_transactions)
                    
                    # Create payout schedule
                    payout_schedule = PayoutSchedule.objects.create(
                        seller=seller,
                        total_amount=total_amount,
                        scheduled_date=scheduled_date,
                        created_by=created_by,
                        notes=notes
                    )
                    
                    # Link transactions to payout schedule
                    payout_schedule.transactions.set(pending_transactions)
                    
                    created_schedules.append(payout_schedule)
                    
                except User.DoesNotExist:
                    errors.append(f"Seller with ID {seller_id} not found")
                except Exception as e:
                    errors.append(f"Error creating payout for seller {seller_id}: {str(e)}")
            
            return {
                'success': len(created_schedules) > 0,
                'created_schedules': created_schedules,
                'errors': errors,
                'message': f'Created {len(created_schedules)} payout schedules'
            }
            
        except Exception as e:
            logger.error(f"Error creating payout schedules: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating payout schedules: {str(e)}'
            }
    
    def process_payouts(self, payout_schedule_ids: List[str], processed_by: User, force_process: bool = False) -> Dict[str, Any]:
        """
        Process multiple payout schedules
        """
        try:
            processed_payouts = []
            errors = []
            
            for schedule_id in payout_schedule_ids:
                try:
                    payout_schedule = PayoutSchedule.objects.get(id=schedule_id)
                    
                    # Check if already processed
                    if payout_schedule.status in ['completed', 'processing']:
                        errors.append(f"Payout {schedule_id} already processed")
                        continue
                    
                    # Check if scheduled date has arrived (unless forced)
                    if not force_process and payout_schedule.scheduled_date > timezone.now().date():
                        errors.append(f"Payout {schedule_id} not yet due")
                        continue
                    
                    # Process the payout
                    result = self.stripe_service.process_payout(payout_schedule)
                    
                    if result['success']:
                        payout_schedule.processed_by = processed_by
                        payout_schedule.save()
                        processed_payouts.append(payout_schedule)
                    else:
                        errors.append(f"Payout {schedule_id}: {result['message']}")
                        
                except PayoutSchedule.DoesNotExist:
                    errors.append(f"Payout schedule {schedule_id} not found")
                except Exception as e:
                    errors.append(f"Error processing payout {schedule_id}: {str(e)}")
            
            return {
                'success': len(processed_payouts) > 0,
                'processed_payouts': processed_payouts,
                'errors': errors,
                'message': f'Processed {len(processed_payouts)} payouts'
            }
            
        except Exception as e:
            logger.error(f"Error processing payouts: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing payouts: {str(e)}'
            }
    
    def get_pending_payouts(self) -> Dict[str, Any]:
        """
        Get all sellers with pending payouts
        """
        try:
            # Get sellers with pending payout transactions
            pending_transactions = Transaction.objects.filter(
                transaction_type='payout',
                status='pending'
            ).select_related('to_user')
            
            # Group by seller
            seller_payouts = {}
            for transaction in pending_transactions:
                seller = transaction.to_user
                if seller.id not in seller_payouts:
                    seller_payouts[seller.id] = {
                        'seller': seller,
                        'total_amount': Decimal('0.00'),
                        'transaction_count': 0,
                        'oldest_transaction': transaction.created_at
                    }
                
                seller_payouts[seller.id]['total_amount'] += transaction.amount
                seller_payouts[seller.id]['transaction_count'] += 1
                
                if transaction.created_at < seller_payouts[seller.id]['oldest_transaction']:
                    seller_payouts[seller.id]['oldest_transaction'] = transaction.created_at
            
            return {
                'success': True,
                'pending_payouts': list(seller_payouts.values()),
                'total_sellers': len(seller_payouts),
                'total_amount': sum(p['total_amount'] for p in seller_payouts.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting pending payouts: {str(e)}")
            return {
                'success': False,
                'message': f'Error getting pending payouts: {str(e)}'
            }


class PaymentStatsProcessor:
    """
    Processor for payment statistics and reporting
    """
    
    def get_payment_stats(self, start_date=None, end_date=None) -> Dict[str, Any]:
        """
        Get payment statistics for a date range
        """
        try:
            # Base queryset
            payment_intents = PaymentIntent.objects.filter(status='succeeded')
            
            if start_date:
                payment_intents = payment_intents.filter(confirmed_at__gte=start_date)
            if end_date:
                payment_intents = payment_intents.filter(confirmed_at__lte=end_date)
            
            # Calculate stats
            total_payments = sum(p.total_amount for p in payment_intents)
            total_commission = sum(p.commission_amount for p in payment_intents)
            payment_count = payment_intents.count()
            
            # Get payout stats
            completed_payouts = PayoutSchedule.objects.filter(status='completed')
            if start_date:
                completed_payouts = completed_payouts.filter(processed_date__gte=start_date)
            if end_date:
                completed_payouts = completed_payouts.filter(processed_date__lte=end_date)
            
            total_payouts = sum(p.total_amount for p in completed_payouts)
            
            # Get pending payouts
            from django.db import models
            pending_payouts = Transaction.objects.filter(
                transaction_type='payout',
                status='pending'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            
            # Get active sellers
            active_sellers = StripeAccount.objects.filter(
                account_status='active'
            ).count()
            
            # Calculate average commission rate
            avg_commission_rate = Decimal('0.00')
            if payment_count > 0:
                avg_commission_rate = sum(p.commission_rate for p in payment_intents) / payment_count
            
            return {
                'success': True,
                'stats': {
                    'total_payments': total_payments,
                    'total_commission': total_commission,
                    'total_payouts': total_payouts,
                    'pending_payouts': pending_payouts,
                    'active_sellers': active_sellers,
                    'payment_count': payment_count,
                    'commission_rate_avg': avg_commission_rate,
                    'currency': 'SEK'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting payment stats: {str(e)}")
            return {
                'success': False,
                'message': f'Error getting payment stats: {str(e)}'
            }
