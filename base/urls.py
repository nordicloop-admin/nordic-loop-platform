from django.urls import path
from .views import SystemStatsView

app_name = 'base'

urlpatterns = [
    # System statistics endpoint
    path('stats/', SystemStatsView.as_view(), name='system-stats'),
]
