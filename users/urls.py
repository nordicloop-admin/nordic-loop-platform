from django.urls import path
from .views import ContactSignupView , ContactLoginView, ListUsersView, UserAdminViewSet
from rest_framework.routers import DefaultRouter


urlpatterns = [
    path("signup/", ContactSignupView.as_view(), name="contact-signup"),
    path("login/", ContactLoginView.as_view(), name="contact-login"),
    path("", ListUsersView.as_view(), name="list-users"),
]

# Admin endpoints
router = DefaultRouter()
router.register(r'admin/users', UserAdminViewSet, basename='admin-users')
urlpatterns += router.urls