from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategorySubscriptionViewSet

router = DefaultRouter()
router.register(r'', CategorySubscriptionViewSet, basename='category-subscriptions')

urlpatterns = [
    path('', include(router.urls)),
]
