from django.urls import path
from .views import BidView, BidDetailView, BidListView, UserBidsView

urlpatterns = [
    path("create/", BidView.as_view(), name="create-bid"),
    path("", BidListView.as_view(), name="list-bids"),  # List bids for an ad (requires ad_id query param)
    path("<int:bid_id>/", BidDetailView.as_view(), name="retrieve-bid"),
    path("<int:bid_id>/update/", BidView.as_view(), name="update-bid"),
    path("<int:bid_id>/delete/", BidView.as_view(), name="delete-bid"),
    path("user/", UserBidsView.as_view(), name="user-bids"),
]