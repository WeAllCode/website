from django.conf.urls import include
from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.AccountHomeView.as_view(),
        name='account_home',
    ),

    path('', include('allauth.urls')),
]
