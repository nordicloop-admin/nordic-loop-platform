from django.urls import path
from bids.views import (
    BidCreateView, BidUpdateView, BidDeleteView, BidDetailView,
    AllBidsListView, AdBidsListView, UserBidsListView, BidHistoryView,
    AdBidStatsView, BidSearchView, WinningBidsView, CloseAuctionView,
    AdminBidListView, AdminBidDetailView,
    BidView  # Legacy view
)

urlpatterns = [
    # Create bid
    path("create/", BidCreateView.as_view(), name="create-bid"),
    
    # Update bid
    path("<int:bid_id>/update/", BidUpdateView.as_view(), name="update-bid"),
    
    # Delete bid
    path("<int:bid_id>/delete/", BidDeleteView.as_view(), name="delete-bid"),
    
    # Bid details
    path("<int:bid_id>/", BidDetailView.as_view(), name="bid-detail"),
    
    # List all bids on platform (with optional filtering)
    path("all/", AllBidsListView.as_view(), name="all-bids"),
    
    # List bids for specific ad
    path("ad/<int:ad_id>/", AdBidsListView.as_view(), name="ad-bids"),
    
    # List current user's bids
    path("my/", UserBidsListView.as_view(), name="user-bids"),
    
    # Bid history for specific bid
    path("<int:bid_id>/history/", BidHistoryView.as_view(), name="bid-history"),
    
    # Bid statistics for specific ad
    path("ad/<int:ad_id>/stats/", AdBidStatsView.as_view(), name="ad-bid-stats"),
    
    # Search bids with filters
    path("search/", BidSearchView.as_view(), name="search-bids"),
    
    # User's winning bids
    path("winning/", WinningBidsView.as_view(), name="winning-bids"),
    
    # Close auction for an ad
    path("ad/<int:ad_id>/close/", CloseAuctionView.as_view(), name="close-auction"),
    
    # Admin endpoints
    path("admin/bids/", AdminBidListView.as_view(), name="admin-bid-list"),
    path("admin/bids/<int:bid_id>/", AdminBidDetailView.as_view(), name="admin-bid-detail"),
    
    # Legacy endpoints for backward compatibility
    path("", BidView.as_view(), name="legacy-bid-create"),
    path("<int:bid_id>/", BidView.as_view(), name="legacy-bid-update-delete"),
]