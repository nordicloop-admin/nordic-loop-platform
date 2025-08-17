from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from decimal import Decimal
from .models import PaymentIntent, Transaction, PayoutSchedule, StripeAccount
from .processors import PayoutProcessor, PaymentStatsProcessor
from .serializers import PayoutScheduleCreateSerializer, PayoutProcessSerializer
import json


@staff_member_required
def payment_dashboard(request):
    """
    Admin dashboard for payment overview
    """
    try:
        # Get payment statistics
        stats_processor = PaymentStatsProcessor()
        stats_result = stats_processor.get_payment_stats()
        
        if stats_result['success']:
            stats = stats_result['stats']
        else:
            stats = {
                'total_payments': Decimal('0.00'),
                'total_commission': Decimal('0.00'),
                'total_payouts': Decimal('0.00'),
                'pending_payouts': Decimal('0.00'),
                'active_sellers': 0,
                'payment_count': 0,
                'commission_rate_avg': Decimal('0.00'),
                'currency': 'SEK'
            }
        
        # Get recent payments
        recent_payments = PaymentIntent.objects.filter(
            status='succeeded'
        ).order_by('-confirmed_at')[:10]
        
        # Get pending payout schedules
        pending_schedules = PayoutSchedule.objects.filter(
            status='scheduled'
        ).order_by('scheduled_date')[:10]
        
        # Get overdue payouts
        overdue_schedules = PayoutSchedule.objects.filter(
            status='scheduled',
            scheduled_date__lt=timezone.now().date()
        ).order_by('scheduled_date')
        
        context = {
            'stats': stats,
            'recent_payments': recent_payments,
            'pending_schedules': pending_schedules,
            'overdue_schedules': overdue_schedules,
            'overdue_count': overdue_schedules.count(),
        }
        
        return render(request, 'admin/payments/dashboard.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading payment dashboard: {str(e)}')
        return render(request, 'admin/payments/dashboard.html', {'stats': {}})


@staff_member_required
def pending_payouts(request):
    """
    Admin view for managing pending payouts
    """
    try:
        payout_processor = PayoutProcessor()
        result = payout_processor.get_pending_payouts()
        
        if result['success']:
            pending_payouts = result['pending_payouts']
            total_amount = result['total_amount']
            total_sellers = result['total_sellers']
        else:
            pending_payouts = []
            total_amount = Decimal('0.00')
            total_sellers = 0
        
        context = {
            'pending_payouts': pending_payouts,
            'total_amount': total_amount,
            'total_sellers': total_sellers,
        }
        
        return render(request, 'admin/payments/pending_payouts.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading pending payouts: {str(e)}')
        return render(request, 'admin/payments/pending_payouts.html', {'pending_payouts': []})


@staff_member_required
def create_payout_schedule(request):
    """
    Admin view for creating payout schedules
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate data
            serializer = PayoutScheduleCreateSerializer(data=data)
            if serializer.is_valid():
                payout_processor = PayoutProcessor()
                result = payout_processor.create_payout_schedule(
                    seller_ids=serializer.validated_data['seller_ids'],
                    scheduled_date=serializer.validated_data['scheduled_date'],
                    created_by=request.user,
                    notes=serializer.validated_data.get('notes', '')
                )
                
                if result['success']:
                    return JsonResponse({
                        'success': True,
                        'message': result['message'],
                        'created_count': len(result['created_schedules']),
                        'errors': result['errors']
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': result['message']
                    }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error creating payout schedule: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)


@staff_member_required
def process_payouts(request):
    """
    Admin view for processing payout schedules
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Validate data
            serializer = PayoutProcessSerializer(data=data)
            if serializer.is_valid():
                payout_processor = PayoutProcessor()
                result = payout_processor.process_payouts(
                    payout_schedule_ids=serializer.validated_data['payout_schedule_ids'],
                    processed_by=request.user,
                    force_process=serializer.validated_data.get('force_process', False)
                )
                
                if result['success']:
                    return JsonResponse({
                        'success': True,
                        'message': result['message'],
                        'processed_count': len(result['processed_payouts']),
                        'errors': result['errors']
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': result['message']
                    }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error processing payouts: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'message': 'Method not allowed'
    }, status=405)


@staff_member_required
def payout_schedules(request):
    """
    Admin view for viewing all payout schedules
    """
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', 'all')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Build queryset
        schedules = PayoutSchedule.objects.all()
        
        if status_filter != 'all':
            schedules = schedules.filter(status=status_filter)
        
        if date_from:
            schedules = schedules.filter(scheduled_date__gte=date_from)
        
        if date_to:
            schedules = schedules.filter(scheduled_date__lte=date_to)
        
        schedules = schedules.order_by('-scheduled_date')
        
        # Get summary statistics
        total_amount = schedules.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        schedule_count = schedules.count()
        
        # Group by status
        status_counts = schedules.values('status').annotate(count=Count('id'))
        
        context = {
            'schedules': schedules,
            'total_amount': total_amount,
            'schedule_count': schedule_count,
            'status_counts': status_counts,
            'status_filter': status_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
        
        return render(request, 'admin/payments/payout_schedules.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading payout schedules: {str(e)}')
        return render(request, 'admin/payments/payout_schedules.html', {'schedules': []})


@staff_member_required
def stripe_accounts(request):
    """
    Admin view for monitoring Stripe accounts
    """
    try:
        # Get filter parameters
        status_filter = request.GET.get('status', 'all')
        
        # Build queryset
        accounts = StripeAccount.objects.select_related('user').all()
        
        if status_filter != 'all':
            accounts = accounts.filter(account_status=status_filter)
        
        accounts = accounts.order_by('-created_at')
        
        # Get summary statistics
        total_accounts = accounts.count()
        active_accounts = accounts.filter(account_status='active').count()
        pending_accounts = accounts.filter(account_status='pending').count()
        restricted_accounts = accounts.filter(account_status='restricted').count()
        
        context = {
            'accounts': accounts,
            'total_accounts': total_accounts,
            'active_accounts': active_accounts,
            'pending_accounts': pending_accounts,
            'restricted_accounts': restricted_accounts,
            'status_filter': status_filter,
        }
        
        return render(request, 'admin/payments/stripe_accounts.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading Stripe accounts: {str(e)}')
        return render(request, 'admin/payments/stripe_accounts.html', {'accounts': []})


@staff_member_required
def payment_details(request, payment_id):
    """
    Admin view for payment details
    """
    try:
        payment = get_object_or_404(PaymentIntent, id=payment_id)
        
        # Get related transactions
        transactions = Transaction.objects.filter(payment_intent=payment)
        
        context = {
            'payment': payment,
            'transactions': transactions,
        }
        
        return render(request, 'admin/payments/payment_details.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading payment details: {str(e)}')
        return redirect('admin:payments_dashboard')
