from django.urls import path
from ads.views import (
    AdStepView, AdDetailView, AdListView, 
    UserAdsView, UserAdsCountView, AdStepValidationView, AdActivateView, AdDeactivateView,
    AdminAuctionListView, AdminAuctionDetailView,
    AdminAddressListView, AdminAddressDetailView, AdminAddressVerifyView,
    AdminSubscriptionListView, AdminSubscriptionDetailView,
    UserSubscriptionView, UpdateUserSubscriptionView,
    UserAddressListView, UserAddressDetailView
)

urlpatterns = [
    # Step-by-step endpoints
    # POST /step/1/ - Create new ad with step 1 data
    # PUT /{ad_id}/step/{1-8}/ - Update steps 1-8
    # GET /{ad_id}/step/{1-8}/ - Get step data
    path("step/<int:step>/", AdStepView.as_view(), name="create-ad-step1"),
    path("<int:ad_id>/step/<int:step>/", AdStepView.as_view(), name="ad-step"),
    
    # Step validation endpoint
    path("validate/step/<int:step>/", AdStepValidationView.as_view(), name="validate-step"),
    
    # Ad management
    path("<int:ad_id>/", AdDetailView.as_view(), name="ad-detail"),
    
    # Ad activation/deactivation
    path("<int:ad_id>/activate/", AdActivateView.as_view(), name="activate-ad"),
    path("<int:ad_id>/deactivate/", AdDeactivateView.as_view(), name="deactivate-ad"),
    
    # List ads with filtering
    path("", AdListView.as_view(), name="list-ads"),
    
    # User's ads
    path("user/", UserAdsView.as_view(), name="user-ads"),
    path("user/count/", UserAdsCountView.as_view(), name="user-ads-count"),
    
    # Admin auction endpoints
    path("admin/auctions/", AdminAuctionListView.as_view(), name="admin-auction-list"),
    path("admin/auctions/<int:ad_id>/", AdminAuctionDetailView.as_view(), name="admin-auction-detail"),
    
    # Admin address endpoints
    path("admin/addresses/", AdminAddressListView.as_view(), name="admin-address-list"),
    path("admin/addresses/<int:address_id>/", AdminAddressDetailView.as_view(), name="admin-address-detail"),
    path("admin/addresses/<int:address_id>/verify/", AdminAddressVerifyView.as_view(), name="admin-address-verify"),
    
    # Admin subscription endpoints
    path("admin/subscriptions/", AdminSubscriptionListView.as_view(), name="admin-subscription-list"),
    path("admin/subscriptions/<int:subscription_id>/", AdminSubscriptionDetailView.as_view(), name="admin-subscription-detail"),
    
    # User subscription endpoints
    path('user/subscription/', UserSubscriptionView.as_view(), name='user-subscription'),
    path('user/subscription/update/', UpdateUserSubscriptionView.as_view(), name='update-user-subscription'),
    
    # User company address endpoints
    path('user/addresses/', UserAddressListView.as_view(), name='user-address-list'),
    path('user/addresses/<int:address_id>/', UserAddressDetailView.as_view(), name='user-address-detail'),
]
