from django.urls import path
from .views import SystemStatsView, UserDashboardStatsView

app_name = 'base'

urlpatterns = [
    # System statistics endpoint
    path('stats/', SystemStatsView.as_view(), name='system-stats'),
    
    # User dashboard statistics endpoint
    path('dashboard/stats/', UserDashboardStatsView.as_view(), name='user-dashboard-stats'),
]
