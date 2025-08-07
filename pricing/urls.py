from django.urls import path
from .views import PricingPlanListView, PricingPageContentView, pricing_data

urlpatterns = [
    path('plans/', PricingPlanListView.as_view(), name='pricing-plans'),
    path('content/', PricingPageContentView.as_view(), name='pricing-content'),
    path('data/', pricing_data, name='pricing-data'),
]
