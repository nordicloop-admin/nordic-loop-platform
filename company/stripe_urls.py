"""
URL patterns for Stripe Connect payment management
"""
from django.urls import path
from .stripe_views import (
    CreateStripeAccountView,
    CreateOnboardingLinkView,
    AccountStatusView,
    CreateDashboardLinkView,
    StripeWebhookView,
)

app_name = 'stripe_connect'

urlpatterns = [
    # Stripe Connect API endpoints
    path('create-account/', CreateStripeAccountView.as_view(), name='create_account'),
    path('create-onboarding-link/', CreateOnboardingLinkView.as_view(), name='create_onboarding_link'),
    path('account-status/', AccountStatusView.as_view(), name='account_status'),
    path('dashboard-link/', CreateDashboardLinkView.as_view(), name='dashboard_link'),
    
    # Webhook endpoint
    path('webhook/', StripeWebhookView.as_view(), name='webhook'),
]