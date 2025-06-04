from django.urls import path
from ads.views import (
    AdCreateView, AdStepView, AdDetailView, AdListView, 
    UserAdsView, AdStepValidationView
)

urlpatterns = [
    # Create new ad (returns ad ID for step completion)
    path("create/", AdCreateView.as_view(), name="create-ad"),
    
    # Step-by-step endpoints
    path("<int:ad_id>/step/<int:step>/", AdStepView.as_view(), name="ad-step"),
    
    # Step validation endpoint
    path("validate/step/<int:step>/", AdStepValidationView.as_view(), name="validate-step"),
    
    # Ad management
    path("<int:ad_id>/", AdDetailView.as_view(), name="ad-detail"),
    
    # List ads with filtering
    path("", AdListView.as_view(), name="list-ads"),
    
    # User's ads
    path("user/", UserAdsView.as_view(), name="user-ads"),
]
