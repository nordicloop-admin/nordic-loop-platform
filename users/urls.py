from django.urls import path
from .views import ContactSignupView, ContactLoginView, ListUsersView, AdminUserListView, AdminUserDetailView, UserProfileView, PasswordChangeView

urlpatterns = [
    path("signup/", ContactSignupView.as_view(), name="contact-signup"),
    path("login/", ContactLoginView.as_view(), name="contact-login"),
    path("", ListUsersView.as_view(), name="list-users"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("change-password/", PasswordChangeView.as_view(), name="change-password"),
    
    # Admin endpoints
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
]