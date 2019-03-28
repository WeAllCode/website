from django.urls import path
from django.conf.urls import include

from . import views


urlpatterns = [
  path(
      '',
      views.MyAccountView.as_view(),
      name='account_home',
  ),

  path('', include('allauth.urls')),
]
