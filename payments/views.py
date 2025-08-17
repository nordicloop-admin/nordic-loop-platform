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
    UserPaymentHistorySerializer
)
from .services import StripeConnectService, CommissionCalculatorService
from .processors import BidPaymentProcessor, PayoutProcessor, PaymentStatsProcessor
import logging

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


class TransactionHistoryView(APIView):
    """
    API view for user transaction history
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's transaction history"""
        # Get transactions where user is involved
        transactions = Transaction.objects.filter(
            models.Q(from_user=request.user) | models.Q(to_user=request.user)
        ).order_by('-created_at')
        
        serializer = TransactionSerializer(transactions, many=True)
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
            return Response(result)
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
