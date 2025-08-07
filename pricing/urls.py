from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PricingPlanListView, PricingPageContentView, pricing_data, BaseFeatureListView,
    AdminBaseFeatureViewSet, AdminPricingPlanViewSet, AdminPlanFeatureViewSet,
    AdminPricingPageContentView, configure_plan_features
)

# Create router for admin viewsets
admin_router = DefaultRouter()
admin_router.register(r'base-features', AdminBaseFeatureViewSet, basename='admin-base-features')
admin_router.register(r'plans', AdminPricingPlanViewSet, basename='admin-pricing-plans')
admin_router.register(r'plan-features', AdminPlanFeatureViewSet, basename='admin-plan-features')

urlpatterns = [
    # Public endpoints
    path('plans/', PricingPlanListView.as_view(), name='pricing-plans'),
    path('base-features/', BaseFeatureListView.as_view(), name='base-features'),
    path('content/', PricingPageContentView.as_view(), name='pricing-content'),
    path('data/', pricing_data, name='pricing-data'),
    path('plans/<int:plan_id>/configure-features/', configure_plan_features, name='configure-plan-features'),

    # Admin endpoints
    path('admin/', include(admin_router.urls)),
    path('admin/content/', AdminPricingPageContentView.as_view(), name='admin-pricing-content'),
]
