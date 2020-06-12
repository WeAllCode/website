from django.conf.urls import include
from django.urls import path

from .views import AccountHomeView, BackgroundCheckView, BackgroundCheckStartedView, LoginView, SignupView

urlpatterns = [
    path('', AccountHomeView.as_view(), name='account_home'),
    path('background/', BackgroundCheckView.as_view(), name='account-background'),
    path('background/started/', BackgroundCheckStartedView.as_view(), name='account-background-started'),
    path('login/', LoginView.as_view(), name='account_login'),
    path('signup/', SignupView.as_view(), name='account_signup'),
    path('', include('allauth.urls')),
]
