from django.urls import path
from .views import ContactSignupView, ContactLoginView, ListUsersView, AdminUserListView, AdminUserDetailView

urlpatterns = [
    path("signup/", ContactSignupView.as_view(), name="contact-signup"),
    path("login/", ContactLoginView.as_view(), name="contact-login"),
    path("", ListUsersView.as_view(), name="list-users"),
    
    # Admin endpoints
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
]