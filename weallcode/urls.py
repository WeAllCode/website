from django.urls import path

from .views import CreditsView, GetInvolvedView, HomeView, OurStoryView, PrivacyView, ProgramsView, TeamView

urlpatterns = [
    path('', HomeView.as_view(), name='weallcode-home'),
    path('our-story/', OurStoryView.as_view(), name='weallcode-our-story'),
    path('programs/', ProgramsView.as_view(), name='weallcode-programs'),
    path('team/', TeamView.as_view(), name='weallcode-team'),
    path('get-involved/', GetInvolvedView.as_view(), name='weallcode-get-involved'),
    path('privacy/', PrivacyView.as_view(), name='weallcode-privacy'),
    path('credits/', CreditsView.as_view(), name='weallcode-credits'),
]
