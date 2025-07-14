from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet

# Create a router and register our viewset with it
router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')

# The API URLs are determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
