import stripe
import logging
import json
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.conf import settings
from .models import PaymentIntent, StripeAccount, PayoutSchedule
from .processors import BidPaymentProcessor

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """
    Handle Stripe webhook events
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    # Development webhook bypass for testing
    DEVELOPMENT_WEBHOOK_BYPASS = (
        getattr(settings, 'DJANGO_DEBUG', False) and
        endpoint_secret.startswith('whsec_test_')
    )

    if DEVELOPMENT_WEBHOOK_BYPASS:
        # For development with test webhook secret, skip signature verification
        logger.info("Using development webhook bypass")
        try:
            event = json.loads(payload.decode('utf-8'))
            # Add a mock event structure if needed
            if 'type' not in event:
                event = {
                    'type': 'payment_intent.succeeded',
                    'data': {'object': event}
                }
        except json.JSONDecodeError:
            logger.error("Invalid JSON payload in development webhook")
            return HttpResponseBadRequest("Invalid JSON payload")
    else:
        # Production webhook signature verification
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            logger.error("Invalid payload in Stripe webhook")
            return HttpResponseBadRequest("Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature in Stripe webhook")
            return HttpResponseBadRequest("Invalid signature")
    
    # Handle the event
    try:
        if event['type'] == 'payment_intent.succeeded':
            handle_payment_intent_succeeded(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            handle_payment_intent_failed(event['data']['object'])
        elif event['type'] == 'account.updated':
            handle_account_updated(event['data']['object'])
        elif event['type'] == 'payout.paid':
            handle_payout_paid(event['data']['object'])
        elif event['type'] == 'payout.failed':
            handle_payout_failed(event['data']['object'])
        else:
            logger.info(f"Unhandled Stripe webhook event: {event['type']}")
        
        return HttpResponse(status=200)
        
    except Exception as e:
        logger.error(f"Error handling Stripe webhook: {str(e)}")
        return HttpResponseBadRequest(f"Webhook error: {str(e)}")


def handle_payment_intent_succeeded(payment_intent_data):
    """
    Handle successful payment intent
    """
    try:
        payment_intent_id = payment_intent_data['id']
        
        # Find our payment intent record
        payment_intent = PaymentIntent.objects.get(
            stripe_payment_intent_id=payment_intent_id
        )
        
        # Update status
        payment_intent.status = 'succeeded'
        payment_intent.save()
        
        # Process the payment completion
        from .completion_services.payment_completion import PaymentCompletionService
        completion_service = PaymentCompletionService()
        result = completion_service.process_payment_completion(payment_intent)

        if result['success']:
            logger.info(f"Payment completion processed successfully: {payment_intent_id}")
        else:
            logger.error(f"Error processing payment completion: {result['message']}")
            
    except PaymentIntent.DoesNotExist:
        logger.error(f"Payment intent not found: {payment_intent_data['id']}")
    except Exception as e:
        logger.error(f"Error handling payment success: {str(e)}")


def handle_payment_intent_failed(payment_intent_data):
    """
    Handle failed payment intent
    """
    try:
        payment_intent_id = payment_intent_data['id']
        
        # Find our payment intent record
        payment_intent = PaymentIntent.objects.get(
            stripe_payment_intent_id=payment_intent_id
        )
        
        # Update status
        payment_intent.status = 'payment_failed'
        payment_intent.save()
        
        # Create notification for buyer
        try:
            from notifications.models import Notification
            
            Notification.objects.create(
                user=payment_intent.buyer,
                title="Payment Failed",
                message=f"Your payment for bid #{payment_intent.bid.id} has failed. Please try again or contact support.",
                type='payment',
                priority='high',
                metadata={
                    'payment_intent_id': str(payment_intent.id),
                    'bid_id': payment_intent.bid.id,
                    'failure_reason': payment_intent_data.get('last_payment_error', {}).get('message', 'Unknown error')
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating payment failure notification: {str(e)}")
        
        logger.info(f"Payment failed: {payment_intent_id}")
        
    except PaymentIntent.DoesNotExist:
        logger.error(f"Payment intent not found: {payment_intent_data['id']}")
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")


def handle_account_updated(account_data):
    """
    Handle Stripe account updates
    """
    try:
        account_id = account_data['id']
        
        # Find our stripe account record
        stripe_account = StripeAccount.objects.get(
            stripe_account_id=account_id
        )
        
        # Update account status
        stripe_account.charges_enabled = account_data.get('charges_enabled', False)
        stripe_account.payouts_enabled = account_data.get('payouts_enabled', False)
        
        # Determine account status
        if stripe_account.charges_enabled and stripe_account.payouts_enabled:
            stripe_account.account_status = 'active'
        elif account_data.get('requirements', {}).get('currently_due'):
            stripe_account.account_status = 'restricted'
        else:
            stripe_account.account_status = 'pending'
        
        stripe_account.save()
        
        # Create notification for user if account is now active
        if stripe_account.account_status == 'active':
            try:
                from notifications.models import Notification
                
                Notification.objects.create(
                    user=stripe_account.user,
                    title="Payment Account Activated",
                    message="Your payment account has been activated and you can now receive payments from sales.",
                    type='account',
                    priority='normal',
                    metadata={
                        'stripe_account_id': account_id,
                        'account_status': 'active'
                    }
                )
                
            except Exception as e:
                logger.error(f"Error creating account activation notification: {str(e)}")
        
        logger.info(f"Account updated: {account_id} - Status: {stripe_account.account_status}")
        
    except StripeAccount.DoesNotExist:
        logger.error(f"Stripe account not found: {account_data['id']}")
    except Exception as e:
        logger.error(f"Error handling account update: {str(e)}")


def handle_payout_paid(payout_data):
    """
    Handle successful payout
    """
    try:
        payout_id = payout_data['id']
        
        # Find our payout schedule record
        payout_schedule = PayoutSchedule.objects.get(
            stripe_payout_id=payout_id
        )
        
        # Update status
        payout_schedule.status = 'completed'
        payout_schedule.save()
        
        # Create notification for seller
        try:
            from notifications.models import Notification
            
            Notification.objects.create(
                user=payout_schedule.seller,
                title="Payout Completed",
                message=f"Your payout of {payout_schedule.total_amount} {payout_schedule.currency} has been sent to your bank account.",
                type='payout',
                priority='normal',
                metadata={
                    'payout_schedule_id': str(payout_schedule.id),
                    'payout_amount': str(payout_schedule.total_amount),
                    'stripe_payout_id': payout_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error creating payout completion notification: {str(e)}")
        
        logger.info(f"Payout completed: {payout_id}")
        
    except PayoutSchedule.DoesNotExist:
        logger.error(f"Payout schedule not found for payout: {payout_data['id']}")
    except Exception as e:
        logger.error(f"Error handling payout completion: {str(e)}")


def handle_payout_failed(payout_data):
    """
    Handle failed payout
    """
    try:
        payout_id = payout_data['id']
        
        # Find our payout schedule record
        payout_schedule = PayoutSchedule.objects.get(
            stripe_payout_id=payout_id
        )
        
        # Update status
        payout_schedule.status = 'failed'
        payout_schedule.save()
        
        # Create notification for seller and admin
        try:
            from notifications.models import Notification
            from users.models import User
            
            # Notify seller
            Notification.objects.create(
                user=payout_schedule.seller,
                title="Payout Failed",
                message=f"Your payout of {payout_schedule.total_amount} {payout_schedule.currency} has failed. Please contact support.",
                type='payout',
                priority='high',
                metadata={
                    'payout_schedule_id': str(payout_schedule.id),
                    'payout_amount': str(payout_schedule.total_amount),
                    'stripe_payout_id': payout_id,
                    'failure_reason': payout_data.get('failure_message', 'Unknown error')
                }
            )
            
            # Notify admin users
            admin_users = User.objects.filter(is_staff=True)
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    title="Payout Failed - Admin Alert",
                    message=f"Payout failed for {payout_schedule.seller.email}: {payout_schedule.total_amount} {payout_schedule.currency}",
                    type='admin',
                    priority='high',
                    metadata={
                        'payout_schedule_id': str(payout_schedule.id),
                        'seller_email': payout_schedule.seller.email,
                        'failure_reason': payout_data.get('failure_message', 'Unknown error')
                    }
                )
            
        except Exception as e:
            logger.error(f"Error creating payout failure notifications: {str(e)}")
        
        logger.error(f"Payout failed: {payout_id}")
        
    except PayoutSchedule.DoesNotExist:
        logger.error(f"Payout schedule not found for payout: {payout_data['id']}")
    except Exception as e:
        logger.error(f"Error handling payout failure: {str(e)}")
