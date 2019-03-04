from django.urls import path

from . import views


urlpatterns = [
    path('',                views.HomeView.as_view()),
    path('our-story',       views.OurStoryView.as_view()),
    path('learn',           views.LearnView.as_view()),
    path('team',            views.TeamView.as_view()),
    path('get-involved',    views.GetInvolvedView.as_view()),
]
