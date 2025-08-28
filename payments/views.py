from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from bids.models import Bid
from .models import StripeAccount, PaymentIntent, Transaction, PayoutSchedule
from .serializers import (
    StripeAccountSerializer, BankAccountSetupSerializer, PaymentIntentSerializer,
    PaymentIntentCreateSerializer, TransactionSerializer, PayoutScheduleSerializer,
    PayoutScheduleCreateSerializer, PayoutProcessSerializer, PaymentStatsSerializer,
    UserPaymentHistorySerializer, PendingPayoutsResponseSerializer
)
from .services import StripeConnectService, CommissionCalculatorService
from .processors import BidPaymentProcessor, PayoutProcessor, PaymentStatsProcessor
from .verification_service import VerificationService
from .completion_services.payment_completion import PaymentCompletionService
import logging
import stripe

logger = logging.getLogger(__name__)


class BankAccountSetupView(APIView):
    """
    API view for setting up seller bank accounts
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BankAccountSetupSerializer(data=request.data)
        if serializer.is_valid():
            stripe_service = StripeConnectService()
            result = stripe_service.create_connect_account(
                request.user, 
                serializer.validated_data
            )
            
            if result['success']:
                account_serializer = StripeAccountSerializer(result['stripe_account'])
                return Response({
                    'success': True,
                    'message': result['message'],
                    'stripe_account': account_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': result['message']
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """Get current user's Stripe account info"""
        try:
            stripe_account = StripeAccount.objects.get(user=request.user)
            serializer = StripeAccountSerializer(stripe_account)
            return Response(serializer.data)
        except StripeAccount.DoesNotExist:
            return Response({
                'message': 'No payment account found'
            }, status=status.HTTP_404_NOT_FOUND)


class VerificationStatusView(APIView):
    """
    API view for checking bank account verification status
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get detailed verification status for current user"""
        verification_service = VerificationService()
        result = verification_service.get_verification_status(request.user)

        if result['success']:
            return Response(result)
        else:
            return Response({
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """Refresh verification status from Stripe"""
        verification_service = VerificationService()
        result = verification_service.refresh_account_status(request.user)

        if result['success']:
            return Response(result)
        else:
            return Response({
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)


class VerificationFAQView(APIView):
    """
    API view for verification FAQ
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get verification FAQ"""
        verification_service = VerificationService()
        faq = verification_service.get_verification_faq()
        return Response(faq)


class PaymentIntentView(APIView):
    """
    API view for creating and managing payment intents
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Create payment intent for a winning bid"""
        serializer = PaymentIntentCreateSerializer(data=request.data)
        if serializer.is_valid():
            bid_id = serializer.validated_data['bid_id']
            
            try:
                bid = Bid.objects.get(id=bid_id, user=request.user, status='won')
                
                processor = BidPaymentProcessor()
                result = processor.process_winning_bid(bid)
                
                if result['success']:
                    payment_serializer = PaymentIntentSerializer(result['payment_intent'])
                    return Response({
                        'success': True,
                        'payment_intent': payment_serializer.data,
                        'client_secret': result['client_secret'],
                        'message': result['message']
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'success': False,
                        'message': result['message']
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Bid.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Winning bid not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """Get user's payment intents"""
        # Get payment intents where user is buyer or seller
        payment_intents = PaymentIntent.objects.filter(
            models.Q(buyer=request.user) | models.Q(seller=request.user)
        ).order_by('-created_at')
        
        serializer = PaymentIntentSerializer(payment_intents, many=True)
        return Response(serializer.data)


class PaymentConfirmationView(APIView):
    """
    API view for confirming payment completion from frontend
    This serves as a fallback when webhooks fail
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, payment_intent_id):
        """Confirm payment completion from frontend"""
        try:
            # Get the payment intent
            payment_intent = PaymentIntent.objects.get(
                id=payment_intent_id,
                buyer=request.user  # Ensure user owns this payment
            )

            # Check if already processed
            if payment_intent.status == 'succeeded':
                return Response({
                    'success': True,
                    'message': 'Payment already confirmed',
                    'already_processed': True
                })

            # Verify with Stripe that payment actually succeeded
            stripe_payment_intent = stripe.PaymentIntent.retrieve(
                payment_intent.stripe_payment_intent_id
            )

            if stripe_payment_intent.status != 'succeeded':
                return Response({
                    'success': False,
                    'message': 'Payment not confirmed by Stripe'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Update payment intent status
            payment_intent.status = 'succeeded'
            payment_intent.save()

            # Process payment completion
            completion_service = PaymentCompletionService()
            result = completion_service.process_payment_completion(payment_intent)

            if result['success']:
                logger.info(f"Payment completion processed via frontend confirmation: {payment_intent_id}")
                return Response({
                    'success': True,
                    'message': 'Payment confirmed and processed successfully',
                    'completion_result': result
                })
            else:
                logger.error(f"Error processing payment completion via frontend: {result['message']}")
                return Response({
                    'success': False,
                    'message': f"Payment confirmed but completion failed: {result['message']}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except PaymentIntent.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Payment intent not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error during payment confirmation: {str(e)}")
            return Response({
                'success': False,
                'message': 'Error verifying payment with Stripe'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}")
            return Response({
                'success': False,
                'message': 'An error occurred while confirming payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransactionHistoryView(APIView):
    """
    API view for user transaction history
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's transaction history with minimal data"""
        # Get transactions where user is involved with optimized queries
        transactions = Transaction.objects.filter(
            models.Q(from_user=request.user) | models.Q(to_user=request.user)
        ).select_related(
            'payment_intent__bid__ad',  # For auction title
            'from_user__company',       # For company names
            'to_user__company'          # For company names
        ).order_by('-created_at')
        
        from .serializers import UserTransactionSerializer
        serializer = UserTransactionSerializer(transactions, many=True, context={'request': request})
        return Response(serializer.data)


class UserPayoutScheduleView(APIView):
    """
    API view for user's payout schedules
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's payout schedules"""
        payout_schedules = PayoutSchedule.objects.filter(
            seller=request.user
        ).order_by('-scheduled_date')
        
        serializer = PayoutScheduleSerializer(payout_schedules, many=True)
        return Response(serializer.data)


# Admin Views
class AdminPaymentStatsView(APIView):
    """
    Admin API view for payment statistics
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get(self, request):
        """Get payment statistics"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        processor = PaymentStatsProcessor()
        result = processor.get_payment_stats(start_date, end_date)
        
        if result['success']:
            return Response(result['stats'])
        else:
            return Response({
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminPendingPayoutsView(APIView):
    """
    Admin API view for managing pending payouts
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get(self, request):
        """Get pending payouts"""
        processor = PayoutProcessor()
        result = processor.get_pending_payouts()

        if result['success']:
            # Serialize the response to handle User objects properly
            serializer = PendingPayoutsResponseSerializer(result)
            return Response(serializer.data)
        else:
            return Response({
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminPayoutScheduleView(APIView):
    """
    Admin API view for creating and managing payout schedules
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def post(self, request):
        """Create payout schedules"""
        serializer = PayoutScheduleCreateSerializer(data=request.data)
        if serializer.is_valid():
            processor = PayoutProcessor()
            result = processor.create_payout_schedule(
                seller_ids=serializer.validated_data['seller_ids'],
                scheduled_date=serializer.validated_data['scheduled_date'],
                created_by=request.user,
                notes=serializer.validated_data.get('notes', '')
            )
            
            if result['success']:
                schedules_serializer = PayoutScheduleSerializer(result['created_schedules'], many=True)
                return Response({
                    'success': True,
                    'created_schedules': schedules_serializer.data,
                    'errors': result['errors'],
                    'message': result['message']
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'message': result['message']
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """Get all payout schedules"""
        payout_schedules = PayoutSchedule.objects.all().order_by('-scheduled_date')
        serializer = PayoutScheduleSerializer(payout_schedules, many=True)
        return Response(serializer.data)


class AdminProcessPayoutsView(APIView):
    """
    Admin API view for processing payouts
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def post(self, request):
        """Process payout schedules"""
        serializer = PayoutProcessSerializer(data=request.data)
        if serializer.is_valid():
            processor = PayoutProcessor()
            result = processor.process_payouts(
                payout_schedule_ids=serializer.validated_data['payout_schedule_ids'],
                processed_by=request.user,
                force_process=serializer.validated_data.get('force_process', False)
            )
            
            if result['success']:
                processed_serializer = PayoutScheduleSerializer(result['processed_payouts'], many=True)
                return Response({
                    'success': True,
                    'processed_payouts': processed_serializer.data,
                    'errors': result['errors'],
                    'message': result['message']
                })
            else:
                return Response({
                    'success': False,
                    'message': result['message']
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminPaymentIntentsView(APIView):
    """
    Admin API view for getting all payment intents
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get(self, request):
        """Get all payment intents for admin dashboard"""
        try:
            payment_intents = PaymentIntent.objects.select_related(
                'bid__user', 
                'bid__ad__user',
                'bid__ad',
                'buyer',
                'buyer__company',
                'seller',
                'seller__company'
            ).order_by('-created_at')
            
            serializer = PaymentIntentSerializer(payment_intents, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching admin payment intents: {str(e)}")
            return Response({
                'error': 'Failed to fetch payment intents'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminTransactionsView(APIView):
    """
    Admin API view for getting all transactions
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get(self, request):
        """Get all transactions for admin dashboard"""
        try:
            transactions = Transaction.objects.select_related(
                'payment_intent__bid__user', 
                'payment_intent__bid__ad__user',
                'payment_intent__bid__ad',
                'payment_intent__buyer',
                'payment_intent__buyer__company',
                'payment_intent__seller',
                'payment_intent__seller__company',
                'from_user',
                'from_user__company',
                'to_user',
                'to_user__company'
            ).order_by('-created_at')
            
            serializer = TransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error fetching admin transactions: {str(e)}")
            return Response({
                'error': 'Failed to fetch transactions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Function-based views for simple operations
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_payment_summary(request):
    """Get user's payment summary"""
    try:
        # Calculate user's payment summary
        user = request.user
        
        # Payments made (as buyer)
        buyer_payments = PaymentIntent.objects.filter(buyer=user, status='succeeded')
        total_spent = sum(p.total_amount for p in buyer_payments)
        total_commission_paid = sum(p.commission_amount for p in buyer_payments)
        
        # Payments received (as seller)
        seller_payments = PaymentIntent.objects.filter(seller=user, status='succeeded')
        total_earned = sum(p.seller_amount for p in seller_payments)
        
        # Pending payouts
        pending_transactions = Transaction.objects.filter(
            to_user=user,
            transaction_type='payout',
            status='pending'
        )
        pending_payouts = sum(t.amount for t in pending_transactions)
        
        # Last payment/payout dates
        last_payment = buyer_payments.order_by('-confirmed_at').first()
        last_payout = PayoutSchedule.objects.filter(
            seller=user, 
            status='completed'
        ).order_by('-processed_date').first()
        
        summary = {
            'user_id': user.id,
            'user_email': user.email,
            'total_spent': total_spent,
            'total_earned': total_earned,
            'total_commission_paid': total_commission_paid,
            'payment_count': buyer_payments.count(),
            'successful_payments': buyer_payments.count(),
            'pending_payouts': pending_payouts,
            'last_payment_date': last_payment.confirmed_at if last_payment else None,
            'last_payout_date': last_payout.processed_date if last_payout else None
        }
        
        return Response(summary)
        
    except Exception as e:
        logger.error(f"Error getting payment summary for user {request.user.id}: {str(e)}")
        return Response({
            'message': 'Error getting payment summary'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
