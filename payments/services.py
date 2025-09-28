import stripe
import logging
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from users.models import User
from ads.models import Subscription
from .models import StripeAccount, PaymentIntent, Transaction, PayoutSchedule
from notifications.models import Notification
from notifications.templates import SellerNotificationTemplates, AdminNotificationTemplates, get_payout_notification_metadata, get_admin_notification_metadata

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
            external_account_data = {
                'object': 'bank_account',
                'country': bank_account_data.get('bank_country', 'SE'),
                'currency': bank_account_data.get('currency', 'sek').lower(),
                'account_holder_name': bank_account_data['account_holder_name'],
                'account_number': bank_account_data['account_number'],
            }
            
            # Only add routing_number if it's provided and not empty
            routing_number = bank_account_data.get('routing_number', '').strip()
            if routing_number:
                external_account_data['routing_number'] = routing_number
            
            bank_account = stripe.Account.create_external_account(
                account.id,
                external_account=external_account_data
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
            # Get seller's Stripe account from their company
            seller = payment_intent_obj.seller
            if not seller.company or not seller.company.stripe_account_id or not seller.company.payment_ready:
                return {
                    'success': False,
                    'message': 'Seller payment account not set up'
                }
            
            seller_company = seller.company

            # Calculate amounts in cents (Stripe uses smallest currency unit)
            total_amount_cents = int(payment_intent_obj.total_amount * 100)
            
            # With platform-hold model, customer always pays platform directly
            # Platform will transfer to seller separately after payment is captured
            intent = stripe.PaymentIntent.create(
                amount=total_amount_cents,
                currency=payment_intent_obj.currency.lower(),
                metadata={
                    'bid_id': payment_intent_obj.bid.id,
                    'buyer_id': payment_intent_obj.buyer.id,
                    'seller_id': payment_intent_obj.seller.id,
                    'seller_account_id': seller_company.stripe_account_id,
                    'commission_rate': str(payment_intent_obj.commission_rate),
                    'commission_amount': str(payment_intent_obj.commission_amount),
                    'seller_amount': str(payment_intent_obj.total_amount - payment_intent_obj.commission_amount),
                    'payment_flow': 'platform_hold_and_transfer',
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
        Process a payout to a seller using platform-hold-and-transfer model
        """
        try:
            # Get seller's company info (new architecture uses Company model)
            seller = payout_schedule.seller
            if not seller.company or not seller.company.stripe_account_id:
                return {
                    'success': False,
                    'message': 'Seller payment account not found'
                }
            
            seller_company = seller.company
            if not seller_company.payment_ready:
                return {
                    'success': False,
                    'message': 'Seller account not ready for payouts'
                }
            
            # Calculate payout amount in cents
            payout_amount_cents = int(payout_schedule.total_amount * 100)
            
            # Create transfer from platform to seller (platform-hold model)
            transfer = stripe.Transfer.create(
                amount=payout_amount_cents,
                currency=payout_schedule.currency.lower(),
                destination=seller_company.stripe_account_id,
                metadata={
                    'payout_schedule_id': str(payout_schedule.id),
                    'seller_id': seller.id,
                    'transfer_type': 'admin_payout',
                    'processed_via': 'admin_dashboard'
                }
            )
            
            # Update payout schedule
            payout_schedule.stripe_payout_id = transfer.id  # Store transfer ID
            payout_schedule.status = 'processing'
            payout_schedule.processed_date = timezone.now().date()
            payout_schedule.save()
            
            # Update related transactions
            payout_schedule.transactions.filter(status='pending').update(
                status='completed',
                processed_at=timezone.now()
            )
            
            # Update related bids' transfer status
            from bids.models import Bid
            related_payment_intents = payout_schedule.transactions.values_list('payment_intent_id', flat=True)
            for payment_intent_id in related_payment_intents:
                if payment_intent_id:
                    try:
                        payment_intent = PaymentIntent.objects.get(id=payment_intent_id)
                        if payment_intent.bid:
                            bid = payment_intent.bid
                            bid.stripe_transfer_id = transfer.id
                            bid.transfer_status = 'completed'
                            bid.transfer_completed_at = timezone.now()
                            bid.save()
                    except (PaymentIntent.DoesNotExist, Bid.DoesNotExist):
                        pass
            
            # Send payout notification to seller
            notification_sent = self._send_payout_notification(
                payout_schedule, transfer.id, requires_manual_processing=False
            )

            return {
                'success': True,
                'payout_id': transfer.id,
                'message': 'Payout transferred successfully',
                'notification_sent': notification_sent
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing payout transfer: {str(e)}")
            
            # Handle insufficient funds error - CRITICAL ADMIN NOTIFICATION REQUIRED
            if 'insufficient available funds' in str(e).lower() or 'available balance' in str(e).lower():
                logger.critical(f"INSUFFICIENT FUNDS: Stripe account has insufficient balance for payout: {str(e)}")
                
                # Mark payout as failed due to insufficient funds
                payout_schedule.status = 'failed'
                payout_schedule.processed_date = timezone.now().date()
                payout_schedule.metadata = {
                    'error': str(e),
                    'insufficient_funds': True,
                    'requires_admin_action': True,
                    'failure_reason': 'Insufficient Stripe account balance'
                }
                payout_schedule.stripe_payout_id = f'failed_{payout_schedule.id}'
                payout_schedule.save()
                
                # Send CRITICAL notification to all admin users
                admin_notification_sent = self._send_admin_insufficient_funds_notification(
                    payout_schedule, str(e)
                )
                
                return {
                    'success': False,
                    'payout_id': f'failed_{payout_schedule.id}',
                    'message': 'Payout failed due to insufficient Stripe account balance. Admin notification sent.',
                    'insufficient_funds': True,
                    'admin_notification_sent': admin_notification_sent,
                    'requires_admin_action': True
                }
            
            # Handle service agreement restrictions for cross-border transfers
            if 'full` service agreement' in str(e) or 'can\'t be sent to accounts located' in str(e):
                logger.warning(f"Cross-border transfer restriction - marking as completed for admin review: {str(e)}")
                
                # Mark payout as failed but requiring manual processing
                payout_schedule.status = 'failed'
                payout_schedule.processed_date = timezone.now().date()
                payout_schedule.metadata = {
                    'error': str(e), 
                    'cross_border_restriction': True,
                    'requires_manual_processing': True,
                    'manual_processing_reason': 'Cross-border transfer restrictions'
                }
                payout_schedule.stripe_payout_id = f'manual_{payout_schedule.id}'
                payout_schedule.save()
                
                # Update related transactions to completed status
                updated_count = payout_schedule.transactions.filter(status='pending').update(
                    status='completed',
                    processed_at=timezone.now()
                )
                
                # Send payout notification to seller for manual processing
                notification_sent = self._send_payout_notification(
                    payout_schedule, f'manual_{payout_schedule.id}', requires_manual_processing=True
                )
                
                return {
                    'success': True,  # Mark as success but with manual flag
                    'payout_id': f'manual_{payout_schedule.id}',
                    'message': f'Payout marked for manual processing due to cross-border restrictions. {updated_count} transactions updated.',
                    'requires_manual_processing': True,
                    'notification_sent': notification_sent
                }
            
            # In test/development mode, we can still mark as processed for testing
            if 'test' in str(e) and ('access' in str(e) or 'account does not exist' in str(e)):
                logger.warning(f"Stripe test account error - marking payout as completed for testing: {str(e)}")
                
                # Update payout schedule to failed status but mark transactions as completed
                payout_schedule.status = 'failed'
                payout_schedule.processed_date = timezone.now().date()
                payout_schedule.metadata = {'error': str(e), 'test_mode_failure': True}
                payout_schedule.save()
                
                # Update related transactions to completed (money is with platform, can be paid manually)
                updated_count = payout_schedule.transactions.filter(status='pending').update(
                    status='completed',
                    processed_at=timezone.now()
                )
                
                # Send payout notification to seller for test mode
                notification_sent = self._send_payout_notification(
                    payout_schedule, f'test_failed_{payout_schedule.id}', requires_manual_processing=True
                )
                
                return {
                    'success': True,  # Mark as success for UI purposes
                    'payout_id': f'test_failed_{payout_schedule.id}',
                    'message': f'Payout marked as processed (Stripe test mode limitation). {updated_count} transactions updated.',
                    'test_mode': True,
                    'notification_sent': notification_sent
                }
            
            return {
                'success': False,
                'message': f'Stripe error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Error processing payout: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing payout: {str(e)}'
            }
    
    def _send_payout_notification(self, payout_schedule: PayoutSchedule, payout_id: str, 
                                 requires_manual_processing: bool = False) -> bool:
        """Send payout processed notification to the seller"""
        try:
            # Check if notification already exists to avoid duplicates
            existing_notification = Notification.objects.filter(
                user=payout_schedule.seller,
                type='payment',
                title__icontains='Payout'
            ).filter(
                metadata__payout_schedule_id=str(payout_schedule.id)
            ).first()
            
            if existing_notification:
                logger.info(f"Payout notification already exists for payout schedule {payout_schedule.id}")
                return True
            
            # Get notification template
            template = SellerNotificationTemplates.payout_processed_notification(
                payout_schedule.total_amount,
                payout_schedule.currency,
                payout_id,
                payout_schedule.transactions.count(),
                requires_manual_processing
            )

            # Generate metadata
            metadata = get_payout_notification_metadata(
                payout_schedule.id,
                payout_id,
                payout_schedule.total_amount,
                payout_schedule.currency,
                payout_schedule.transactions.count(),
                payout_schedule.seller.id,
                requires_manual_processing
            )

            # Create the notification
            Notification.objects.create(
                user=payout_schedule.seller,
                title=template['title'],
                message=template['message'],
                type='payment',
                priority='high',
                action_url='/dashboard/payments',
                metadata=metadata
            )
            
            logger.info(f"Payout notification sent for payout schedule {payout_schedule.id} to seller {payout_schedule.seller.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending payout notification for payout schedule {payout_schedule.id}: {str(e)}")
            return False
    
    def _send_admin_insufficient_funds_notification(self, payout_schedule: PayoutSchedule, stripe_error: str) -> bool:
        """Send critical notification to all admin users about insufficient Stripe funds"""
        try:
            # Get all admin users
            admin_users = User.objects.filter(is_staff=True, is_superuser=True, is_active=True)
            
            if not admin_users.exists():
                logger.error("No admin users found to send insufficient funds notification")
                return False
            
            notifications_created = 0
            
            for admin_user in admin_users:
                # Check if notification already exists for this payout to avoid duplicates
                existing_notification = Notification.objects.filter(
                    user=admin_user,
                    type='system',
                    title__icontains='Insufficient Stripe Balance'
                ).filter(
                    metadata__payout_schedule_id=str(payout_schedule.id)
                ).first()
                
                if existing_notification:
                    logger.info(f"Insufficient funds notification already exists for admin {admin_user.email} and payout {payout_schedule.id}")
                    continue
                
                # Get notification template
                template = AdminNotificationTemplates.insufficient_funds_notification(
                    payout_schedule.total_amount,
                    payout_schedule.currency,
                    payout_schedule.seller.email,
                    str(payout_schedule.id),
                    stripe_error
                )

                # Generate metadata
                metadata = get_admin_notification_metadata(
                    str(payout_schedule.id),
                    payout_schedule.seller.id,
                    payout_schedule.seller.email,
                    payout_schedule.total_amount,
                    payout_schedule.currency,
                    stripe_error,
                    'insufficient_funds_alert'
                )

                # Create the CRITICAL notification
                Notification.objects.create(
                    user=admin_user,
                    title=template['title'],
                    message=template['message'],
                    type='system',
                    priority='urgent',  # Highest priority for admin alerts
                    action_url='/admin/payments/payoutschedule/',  # Direct link to admin payout management
                    metadata=metadata
                )
                
                notifications_created += 1
            
            logger.critical(f"CRITICAL: Sent insufficient funds notification to {notifications_created} admin users for payout schedule {payout_schedule.id}")
            return notifications_created > 0
            
        except Exception as e:
            logger.error(f"Error sending admin insufficient funds notification for payout schedule {payout_schedule.id}: {str(e)}")
            return False


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
