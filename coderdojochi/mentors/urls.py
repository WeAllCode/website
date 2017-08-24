from django.conf.urls import url

from .views import VolunteerView

# Volunteer
# /volunteer/
urlpatterns = [
    url(
        r'^$',
        VolunteerView.as_view(),
        name='volunteer',
    ),
]
