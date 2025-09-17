from django.urls import path, include
from . import views, webhooks, admin_views, subscription_views

app_name = 'payments'

urlpatterns = [
    # Subscription payment endpoints
    path('subscriptions/checkout/', subscription_views.create_subscription_checkout, name='subscription_checkout'),
    path('subscriptions/cancel/', subscription_views.cancel_subscription, name='subscription_cancel'),
    path('subscriptions/status/', subscription_views.get_subscription_status, name='subscription_status'),
    path('subscriptions/verify-session/', subscription_views.verify_checkout_session, name='verify_checkout_session'),
    path('subscriptions/webhook/', subscription_views.subscription_webhook, name='subscription_webhook'),
    
    # User payment endpoints
    path('bank-account/', views.BankAccountSetupView.as_view(), name='bank_account_setup'),
    path('verification-status/', views.VerificationStatusView.as_view(), name='verification_status'),
    path('verification-faq/', views.VerificationFAQView.as_view(), name='verification_faq'),
    path('payment-intent/', views.PaymentIntentView.as_view(), name='payment_intent'),
    path('payment-intent/<uuid:payment_intent_id>/confirm/', views.PaymentConfirmationView.as_view(), name='payment_confirmation'),
    path('transactions/', views.TransactionHistoryView.as_view(), name='transaction_history'),
    path('payouts/', views.UserPayoutScheduleView.as_view(), name='user_payouts'),
    path('summary/', views.user_payment_summary, name='payment_summary'),
    
    # Transfer endpoints (platform hold and transfer model)
    path('bids/<int:bid_id>/transfer/', views.transfer_to_seller, name='transfer_to_seller'),
    path('bids/<int:bid_id>/payment-status/', views.payment_status, name='bid_payment_status'),
    
    # Admin payment endpoints
    path('admin/stats/', views.AdminPaymentStatsView.as_view(), name='admin_payment_stats'),
    path('admin/pending-payouts/', views.AdminPendingPayoutsView.as_view(), name='admin_pending_payouts'),
    path('admin/payout-schedules/', views.AdminPayoutScheduleView.as_view(), name='admin_payout_schedules'),
    path('admin/process-payouts/', views.AdminProcessPayoutsView.as_view(), name='admin_process_payouts'),
    path('admin/payment-intents/', views.AdminPaymentIntentsView.as_view(), name='admin_payment_intents'),
    path('admin/transactions/', views.AdminTransactionsView.as_view(), name='admin_transactions'),
    
    # Stripe webhooks
    path('webhooks/stripe/', webhooks.stripe_webhook, name='stripe_webhook'),
]
