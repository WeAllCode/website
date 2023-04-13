from django.conf.urls import include
from django.urls import path

from .views import (
    AccountHomeView,
    LoginView,
    SignupView,
)

urlpatterns = [
    path("", AccountHomeView.as_view(), name="account_home"),
    path("login/", LoginView.as_view(), name="account_login"),
    path("signup/", SignupView.as_view(), name="account_signup"),
    path("", include("allauth.urls")),
]
