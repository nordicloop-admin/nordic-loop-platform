from django.urls import path, include
from . import views, webhooks, admin_views

app_name = 'payments'

urlpatterns = [
    # User payment endpoints
    path('bank-account/', views.BankAccountSetupView.as_view(), name='bank_account_setup'),
    path('payment-intent/', views.PaymentIntentView.as_view(), name='payment_intent'),
    path('transactions/', views.TransactionHistoryView.as_view(), name='transaction_history'),
    path('payouts/', views.UserPayoutScheduleView.as_view(), name='user_payouts'),
    path('summary/', views.user_payment_summary, name='payment_summary'),
    
    # Admin payment endpoints
    path('admin/stats/', views.AdminPaymentStatsView.as_view(), name='admin_payment_stats'),
    path('admin/pending-payouts/', views.AdminPendingPayoutsView.as_view(), name='admin_pending_payouts'),
    path('admin/payout-schedules/', views.AdminPayoutScheduleView.as_view(), name='admin_payout_schedules'),
    path('admin/process-payouts/', views.AdminProcessPayoutsView.as_view(), name='admin_process_payouts'),
    
    # Stripe webhooks
    path('webhooks/stripe/', webhooks.stripe_webhook, name='stripe_webhook'),
]
