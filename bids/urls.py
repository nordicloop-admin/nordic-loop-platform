from django.urls import path
from .views import BidView

urlpatterns = [
    path("create/", BidView.as_view(), name="create-bid"),            
    path("", BidView.as_view(), name="list-bids"),                    
    path("<int:bid_id>/", BidView.as_view(), name="retrieve-bid"),   
    path("<int:bid_id>/delete/", BidView.as_view(), name="delete-bid"), 
    path("user/", BidView.as_view(), name="user-bids"),
]