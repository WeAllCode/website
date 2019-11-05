from django.conf.urls import include
from django.urls import path

from .views import AccountHomeView, LoginView, SignupView

urlpatterns = [
    path('', AccountHomeView.as_view(), name='account-home'),
    path('payments/', PaymentsView.as_view(), name='account-payments',),
    path('login/', LoginView.as_view(), name='account_login'),
    path('signup/', SignupView.as_view(), name='account_signup'),
    path('', include('allauth.urls')),
]
