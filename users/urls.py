from django.urls import path
from .views import ContactSignupView, ContactLoginView, ListUsersView, AdminUserListView, AdminUserDetailView, UserProfileView, PasswordChangeView, UserCompanySearchView
from .views_password_reset import (
    RequestPasswordResetView,
    VerifyOtpView,
    ResetPasswordView,
    RequestActivationOtpView,
    VerifyActivationOtpView,
    ActivateAccountSetPasswordView,
)

urlpatterns = [
    path("signup/", ContactSignupView.as_view(), name="contact-signup"),
    path("login/", ContactLoginView.as_view(), name="contact-login"),
    path("", ListUsersView.as_view(), name="list-users"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("change-password/", PasswordChangeView.as_view(), name="change-password"),
    path("search/", UserCompanySearchView.as_view(), name="user-company-search"),
    
    # Password reset endpoints
    path("request-password-reset/", RequestPasswordResetView.as_view(), name="request-password-reset"),
    path("verify-otp/", VerifyOtpView.as_view(), name="verify-otp"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
    # Activation flow
    path("request-activation-otp/", RequestActivationOtpView.as_view(), name="request-activation-otp"),
    path("verify-activation-otp/", VerifyActivationOtpView.as_view(), name="verify-activation-otp"),
    path("activate-set-password/", ActivateAccountSetPasswordView.as_view(), name="activate-set-password"),
    
    # Admin endpoints
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
]