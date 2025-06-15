from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    BidCreateView, BidUpdateView, BidDeleteView, BidDetailView,
    AdBidsListView, AllBidsListView, UserBidsListView, BidHistoryView, AdBidStatsView,
    BidSearchView, WinningBidsView, CloseAuctionView, BidView, BidAdminViewSet
)

urlpatterns = [
    # General bid listing
    path("", AllBidsListView.as_view(), name="all-bids-list"),
    
    # New enhanced endpoints
    path("create/", BidCreateView.as_view(), name="create-bid"),
    path("<int:bid_id>/", BidDetailView.as_view(), name="bid-detail"),
    path("<int:bid_id>/update/", BidUpdateView.as_view(), name="update-bid"),
    path("<int:bid_id>/delete/", BidDeleteView.as_view(), name="delete-bid"),
    path("<int:bid_id>/history/", BidHistoryView.as_view(), name="bid-history"),
    
    # Ad-related bid endpoints
    path("ad/<int:ad_id>/", AdBidsListView.as_view(), name="ad-bids-list"),
    path("ad/<int:ad_id>/stats/", AdBidStatsView.as_view(), name="ad-bid-stats"),
    path("ad/<int:ad_id>/close/", CloseAuctionView.as_view(), name="close-auction"),
    
    # User bid management
    path("user/", UserBidsListView.as_view(), name="user-bids"),
    path("user/winning/", WinningBidsView.as_view(), name="user-winning-bids"),
    
    # Search and filtering
    path("search/", BidSearchView.as_view(), name="bid-search"),
    
    # Legacy endpoints (for backward compatibility)
    path("legacy/create/", BidView.as_view(), name="legacy-create-bid"),
    path("legacy/<int:bid_id>/update/", BidView.as_view(), name="legacy-update-bid"),
    path("legacy/<int:bid_id>/delete/", BidView.as_view(), name="legacy-delete-bid"),
]

# Admin endpoints
router = DefaultRouter()
router.register(r'admin/bids', BidAdminViewSet, basename='admin-bids')
urlpatterns += router.urls