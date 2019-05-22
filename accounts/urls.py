from django.conf.urls import include
from django.urls import path

from .views import AccountHomeView, PaymentsView

urlpatterns = [
    path('', AccountHomeView.as_view(), name='account-home',),
    path('payments/', PaymentsView.as_view(), name='account-payments',),

    path('', include('allauth.urls')),
]
