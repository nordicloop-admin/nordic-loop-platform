"""
Subscription API views for handling subscription payments via Stripe
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
import stripe
import logging
import json

from .subscription_service import StripeSubscriptionService
from ads.models import Subscription
from pricing.models import PricingPlan
from users.models import User
from company.models import Company

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subscription_checkout(request):
    """
    Create a Stripe Checkout session for subscription payment
    """
    try:
        user = request.user
        plan_type = request.data.get('plan_type')
        
        if not plan_type:
            return Response({
                'success': False,
                'message': 'Plan type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate plan type
        valid_plans = ['free', 'standard', 'premium']
        if plan_type not in valid_plans:
            return Response({
                'success': False,
                'message': f'Invalid plan type. Must be one of: {", ".join(valid_plans)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's company
        try:
            company = Company.objects.get(user=user)
        except Company.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Company profile not found. Please complete your company profile first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create subscription checkout
        subscription_service = StripeSubscriptionService()
        result = subscription_service.create_subscription_checkout(user, company, plan_type)
        
        if result['success']:
            return Response({
                'success': True,
                'checkout_url': result.get('checkout_url'),
                'session_id': result.get('session_id'),
                'message': result['message']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error creating subscription checkout: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error creating checkout: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_subscription(request):
    """
    Cancel user's subscription
    """
    try:
        user = request.user
        
        # Get user's company
        try:
            company = Company.objects.get(user=user)
        except Company.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Company profile not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel subscription
        subscription_service = StripeSubscriptionService()
        result = subscription_service.cancel_subscription(user, company)
        
        return Response({
            'success': result['success'],
            'message': result['message']
        }, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error canceling subscription: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_subscription_plan(request):
    """
    Change user's subscription plan (upgrade/downgrade)
    """
    try:
        user = request.user
        plan_type = request.data.get('plan_type')
        
        if not plan_type:
            return Response({
                'success': False,
                'message': 'Plan type is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if plan_type not in ['free', 'standard', 'premium']:
            return Response({
                'success': False,
                'message': 'Invalid plan type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user's company
        try:
            company = Company.objects.get(user=user)
        except Company.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Company profile not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Change subscription plan
        subscription_service = StripeSubscriptionService()
        result = subscription_service.change_subscription_plan(user, company, plan_type)
        
        if result['success']:
            response_data = {
                'success': True,
                'message': result['message']
            }
            
            # Add checkout URL if payment is needed
            if result.get('checkout_url'):
                response_data['redirect_url'] = result['checkout_url']
                response_data['session_id'] = result.get('session_id')
            
            # Indicate if it's a free plan
            if result.get('is_free_plan'):
                response_data['is_free_plan'] = True
            
            # Indicate if change was prorated
            if result.get('prorated'):
                response_data['prorated'] = True
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error changing subscription plan: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error changing subscription plan: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subscription_status(request):
    """
    Get current subscription status
    """
    try:
        user = request.user
        
        # Get user's company
        try:
            company = Company.objects.get(user=user)
        except Company.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Company profile not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get subscription status
        subscription_service = StripeSubscriptionService()
        result = subscription_service.get_subscription_status(user, company)
        
        if result['success']:
            subscription_data = None
            if result.get('subscription'):
                sub = result['subscription']
                subscription_data = {
                    'plan': sub.plan,
                    'status': sub.status,
                    'start_date': sub.start_date,
                    'end_date': sub.end_date,
                    'auto_renew': sub.auto_renew,
                    'last_payment': sub.last_payment,
                    'next_billing_date': sub.next_billing_date,
                    'amount': sub.amount,
                    'contact_name': sub.contact_name,
                    'contact_email': sub.contact_email,
                    'stripe_customer_id': sub.stripe_customer_id,
                    'stripe_subscription_id': sub.stripe_subscription_id,
                    'cancel_at_period_end': sub.cancel_at_period_end,
                    'canceled_at': sub.canceled_at.isoformat() if sub.canceled_at else None,
                    'trial_end': sub.trial_end.isoformat() if sub.trial_end else None,
                }
            
            return Response({
                'success': True,
                'subscription': subscription_data,
                'has_subscription': result['has_subscription'],
                'message': result['message']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error getting subscription status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_checkout_session(request):
    """
    Verify a Stripe checkout session and update subscription status
    """
    try:
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response({
                'success': False,
                'message': 'Session ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Retrieve the checkout session from Stripe
        try:
            stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
            session = stripe.checkout.Session.retrieve(session_id)
        except stripe.StripeError as e:
            logger.error(f"Stripe error retrieving session {session_id}: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error retrieving checkout session: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if session.payment_status == 'paid':
            # Session was successful
            return Response({
                'success': True,
                'payment_status': session.payment_status,
                'subscription_id': session.subscription,
                'message': 'Payment successful'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'payment_status': session.payment_status,
                'message': f'Payment not completed. Status: {session.payment_status}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error verifying checkout session: {str(e)}")
        return Response({
            'success': False,
            'message': f'Error verifying session: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_POST
def subscription_webhook(request):
    """
    Handle Stripe subscription webhooks
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
    
    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        else:
            # For development/testing without webhook secret
            event = stripe.Event.construct_from(
                json.loads(payload), stripe.api_key
            )
    except ValueError:
        logger.error("Invalid payload in subscription webhook")
        return HttpResponse(status=400)
    except stripe.SignatureVerificationError:
        logger.error("Invalid signature in subscription webhook")
        return HttpResponse(status=400)
    
    # Handle the event
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_checkout_session_completed(session)
        
        elif event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            handle_subscription_created(subscription)
        
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            handle_subscription_updated(subscription)
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            handle_subscription_deleted(subscription)
        
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            handle_invoice_payment_succeeded(invoice)
        
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            handle_invoice_payment_failed(invoice)
        
        else:
            logger.info(f"Unhandled event type: {event['type']}")
    
    except Exception as e:
        logger.error(f"Error handling subscription webhook event {event.get('type', 'unknown')}: {str(e)}")
        return HttpResponse(status=500)
    
    return HttpResponse(status=200)


def handle_checkout_session_completed(session):
    """Handle completed checkout session"""
    try:
        logger.info(f"Checkout session completed: {session['id']}")
        
        # If there's a subscription, it will be handled by the subscription.created event
        # For one-time payments, handle them here if needed
        if session.get('subscription'):
            logger.info(f"Subscription {session['subscription']} created from checkout session {session['id']}")
        
    except Exception as e:
        logger.error(f"Error handling checkout session completed: {str(e)}")


def handle_subscription_created(stripe_subscription):
    """Handle subscription creation"""
    try:
        logger.info(f"Subscription created: {stripe_subscription['id']}")
        
        subscription_service = StripeSubscriptionService()
        
        # Convert dict to Stripe object if needed
        if isinstance(stripe_subscription, dict):
            stripe_subscription = stripe.Subscription.construct_from(
                stripe_subscription, stripe.api_key
            )
        
        result = subscription_service.handle_subscription_created(stripe_subscription)
        
        if result['success']:
            logger.info(f"Successfully processed subscription creation: {stripe_subscription['id']}")
        else:
            logger.error(f"Failed to process subscription creation: {result['message']}")
    
    except Exception as e:
        logger.error(f"Error handling subscription created: {str(e)}")


def handle_subscription_updated(stripe_subscription):
    """Handle subscription updates"""
    try:
        logger.info(f"Subscription updated: {stripe_subscription['id']}")
        
        # Handle subscription updates (plan changes, etc.)
        metadata = stripe_subscription.get('metadata', {})
        company_id = metadata.get('company_id')
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                subscription = Subscription.objects.get(company=company)
                
                # Update status based on Stripe subscription status
                if stripe_subscription['status'] == 'active':
                    subscription.status = 'active'
                elif stripe_subscription['status'] in ['canceled', 'unpaid']:
                    subscription.status = 'expired'
                elif stripe_subscription['status'] == 'past_due':
                    subscription.status = 'payment_failed'
                
                subscription.save()
                
                logger.info(f"Updated subscription status for company {company.official_name}")
            
            except (Company.DoesNotExist, Subscription.DoesNotExist):
                logger.error(f"Could not find local subscription for Stripe subscription {stripe_subscription['id']}")
    
    except Exception as e:
        logger.error(f"Error handling subscription updated: {str(e)}")


def handle_subscription_deleted(stripe_subscription):
    """Handle subscription cancellation"""
    try:
        logger.info(f"Subscription deleted: {stripe_subscription['id']}")
        
        metadata = stripe_subscription.get('metadata', {})
        company_id = metadata.get('company_id')
        
        if company_id:
            try:
                company = Company.objects.get(id=company_id)
                subscription = Subscription.objects.get(company=company)
                
                subscription.status = 'expired'
                subscription.auto_renew = False
                subscription.save()
                
                logger.info(f"Canceled subscription for company {company.official_name}")
            
            except (Company.DoesNotExist, Subscription.DoesNotExist):
                logger.error(f"Could not find local subscription for Stripe subscription {stripe_subscription['id']}")
    
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {str(e)}")


def handle_invoice_payment_succeeded(invoice):
    """Handle successful invoice payment"""
    try:
        logger.info(f"Invoice payment succeeded: {invoice['id']}")
        
        subscription_id = invoice.get('subscription')
        if subscription_id:
            # Update last payment date
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            metadata = stripe_subscription.metadata
            company_id = metadata.get('company_id')
            
            if company_id:
                try:
                    company = Company.objects.get(id=company_id)
                    subscription = Subscription.objects.get(company=company)
                    
                    subscription.status = 'active'
                    subscription.last_payment = timezone.now().date()
                    subscription.save()
                    
                    logger.info(f"Updated payment date for company {company.official_name}")
                
                except (Company.DoesNotExist, Subscription.DoesNotExist):
                    logger.error(f"Could not find local subscription for invoice {invoice['id']}")
    
    except Exception as e:
        logger.error(f"Error handling invoice payment succeeded: {str(e)}")


def handle_invoice_payment_failed(invoice):
    """Handle failed invoice payment"""
    try:
        logger.info(f"Invoice payment failed: {invoice['id']}")
        
        subscription_id = invoice.get('subscription')
        if subscription_id:
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            metadata = stripe_subscription.metadata
            company_id = metadata.get('company_id')
            
            if company_id:
                try:
                    company = Company.objects.get(id=company_id)
                    subscription = Subscription.objects.get(company=company)
                    
                    subscription.status = 'payment_failed'
                    subscription.save()
                    
                    logger.info(f"Updated payment failed status for company {company.official_name}")
                
                except (Company.DoesNotExist, Subscription.DoesNotExist):
                    logger.error(f"Could not find local subscription for invoice {invoice['id']}")
    
    except Exception as e:
        logger.error(f"Error handling invoice payment failed: {str(e)}")
