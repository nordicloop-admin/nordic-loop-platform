from django.urls import path
from ads.views import (
    AdStepView, AdDetailView, AdListView, 
    UserAdsView, AdStepValidationView, AdActivateView, AdDeactivateView
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
]
