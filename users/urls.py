from django.urls import path
from .views import ContactSignupView , ContactLoginView, ListUsersView


urlpatterns = [
    path("signup/", ContactSignupView.as_view(), name="contact-signup"),
    path("login/", ContactLoginView.as_view(), name="contact-login"),
    path("", ListUsersView.as_view(), name="list-users"),
]