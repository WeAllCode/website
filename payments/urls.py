# from django.conf import settings
from django.conf.urls import include, url
# from django.conf.urls.static import static
# from django.contrib import admin
# from django.contrib.auth import views as django_views
# from django.http import HttpResponse
# from django.urls import path
# from django.views import defaults
# from django.views.generic import RedirectView
# from loginas import views as loginas_views
from django.urls import path

from .views import DonateView

urlpatterns = [

]


urlpatterns += [
    path('', include([
        # Donation
        # /donate/
        # path('', views.donate, name='donate'),

        path('', DonateView.as_view(), name='donate'),

        # /donate/charge
        # path('charge/', views.donate_charge, name='donate-charge'),

        # /donate/cancel/
        # path('cancel/', payments.donate_cancel, name='donate-cancel'),

        # /donate/return/
        # path('return/', payments.donate_return, name='donate-return'),

        # /donate/paypal/
        # path('paypal/', include('paypal.standard.ipn.urls')),
    ])),
]
