from django.urls import path

from . import views

urlpatterns = [
    path(
        '',
        views.HomeView.as_view(),
        name='weallcode_home',
    ),

    path(
        'our-story',
        views.OurStoryView.as_view(),
        name='weallcode_our_story',
    ),

    path(
        'programs',
        views.ProgramsView.as_view(),
        name='weallcode_programs',
    ),

    path(
        'team',
        views.TeamView.as_view(),
        name='weallcode_team',
    ),

    path(
        'get-involved',
        views.GetInvolvedView.as_view(),
        name='weallcode_get_involved',
    ),

    path(
        'contact',
        views.ContactView.as_view(),
        name='weallcode_contact',
    ),

    path(
        'privacy',
        views.PrivacyView.as_view(),
        name='weallcode_privacy',
    ),

    path(
        'credits',
        views.CreditsView.as_view(),
        name='weallcode_credits',
    ),
]
