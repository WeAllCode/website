from django.urls import path

from . import views


urlpatterns = [
    path('',                views.HomeView.as_view(),           name='weallcode_home'),
    path('our-story',       views.OurStoryView.as_view(),       name='weallcode_our_story'),
    path('learn',           views.LearnView.as_view(),          name='weallcode_learn'),
    path('team',            views.TeamView.as_view(),           name='weallcode_team'),
    path('get-involved',    views.GetInvolvedView.as_view(),    name='weallcode_get_involved'),
]
