"""
API views for Stripe Connect payment account management
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.conf import settings
import stripe
import json
import logging
from .stripe_service import StripeConnectService
from .models import Company

logger = logging.getLogger(__name__)

class CreateStripeAccountView(APIView):
    """Create a new Stripe Express account for the user's company"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Check if user has a company
            if not hasattr(request.user, 'company') or not request.user.company:
                return Response({
                    'error': 'No company associated with this user. Please create a company first.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            company = request.user.company
            
            # Check if account already exists
            if company.stripe_account_id:
                return Response({
                    'error': 'Stripe account already exists for this company',
                    'account_id': company.stripe_account_id
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create Stripe Express account with onboarding URL
            success, message, account_id, onboarding_url = StripeConnectService.create_express_account(
                company, request.user.email, request
            )
            
            if success:
                response_data = {
                    'message': message,
                    'account_id': account_id,
                    'next_step': 'onboarding'
                }
                
                # Add onboarding URL if available
                if onboarding_url:
                    response_data['onboarding_url'] = onboarding_url
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating Stripe account: {str(e)}")
            return Response({
                'error': 'Failed to create payment account'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateOnboardingLinkView(APIView):
    """Create an onboarding link for Stripe Express account"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Check if user has a company
            if not hasattr(request.user, 'company') or not request.user.company:
                return Response({
                    'error': 'No company associated with this user'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            company = request.user.company
            
            # Check if Stripe account exists
            if not company.stripe_account_id:
                return Response({
                    'error': 'No Stripe account found. Please create an account first.',
                    'action_needed': 'create_account'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create onboarding link
            success, message, onboarding_url = StripeConnectService.create_account_link(
                company, request
            )
            
            if success:
                return Response({
                    'message': message,
                    'onboarding_url': onboarding_url
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating onboarding link: {str(e)}")
            return Response({
                'error': 'Failed to create onboarding link'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AccountStatusView(APIView):
    """Get the current status of the Stripe Connect account"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Check if user has a company
            if not hasattr(request.user, 'company') or not request.user.company:
                return Response({
                    'error': 'No company associated with this user',
                    'account_status': 'no_company'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            company = request.user.company
            
            # Get account status
            account_info = StripeConnectService.check_account_status(company)
            
            # Add company payment status
            response_data = {
                'company_id': company.id,
                'company_name': company.official_name,
                'payment_ready': company.payment_ready,
                'stripe_onboarding_complete': company.stripe_onboarding_complete,
                'stripe_capabilities_complete': company.stripe_capabilities_complete,
                'account_info': account_info
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Error getting account status: {str(e)}")
            return Response({
                'error': 'Failed to get account status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateDashboardLinkView(APIView):
    """Create a login link to Stripe Express dashboard"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Check if user has a company
            if not hasattr(request.user, 'company') or not request.user.company:
                return Response({
                    'error': 'No company associated with this user'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            company = request.user.company
            
            # Check if account is ready
            if not company.payment_ready:
                return Response({
                    'error': 'Account setup is not complete. Please finish onboarding first.',
                    'action_needed': 'complete_onboarding'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create dashboard login link
            success, message, login_url = StripeConnectService.create_login_link(company)
            
            if success:
                return Response({
                    'message': message,
                    'dashboard_url': login_url
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': message
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating dashboard link: {str(e)}")
            return Response({
                'error': 'Failed to create dashboard link'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """Handle Stripe webhooks for account updates"""
    permission_classes = []  # No authentication required for webhooks
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload in webhook: {e}")
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature in webhook: {e}")
            return HttpResponse(status=400)
        
        # Handle the event
        try:
            if event['type'] == 'account.updated':
                account = event['data']['object']
                account_id = account['id']
                
                # Update account status
                StripeConnectService.handle_account_update_webhook(account_id)
                logger.info(f"Processed account.updated webhook for {account_id}")
                
            else:
                logger.info(f"Received unhandled webhook event: {event['type']}")
            
            return HttpResponse(status=200)
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return HttpResponse(status=500)