from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as django_views
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse
from django.urls import path
from django.views import defaults
from django.views.generic import RedirectView

from loginas import views as loginas_views

from . import old_views
from .views.general import AboutView, HomeView, PrivacyView, WelcomeView
from .views.meetings import (
    MeetingCalendarView,
    MeetingDetailRedirectView,
    MeetingDetailView,
    MeetingsView,
    meeting_announce,
    meeting_sign_up
)
from .views.profile import DojoMentorView
from .views.sessions import (
    PasswordSessionRedirectView,
    PasswordSessionView,
    SessionCalendarRedirectView,
    SessionCalendarView,
    SessionDetailRedirectView,
    SessionDetailView,
    SessionSignUpRedirectView,
    SessionSignUpView,
    SessionsRedirectView,
    SessionsView
)
from .views.volunteer import VolunteerView

admin.autodiscover()

# Empty to start
urlpatterns = []

# General
urlpatterns += [
    # /
    # old_views.home,
    path('', HomeView.as_view(), name='home'),

    # About
    # /about/
    path('about/', AboutView.as_view(), name='about'),

    # Volunteer
    # /volunteer/
    path('volunteer/', VolunteerView.as_view(), name='volunteer'),

    # Contact
    # /contact/
    path('contact/', old_views.contact, name='contact'),

    # Privacy
    # /privary/
    path('privacy/', PrivacyView.as_view(), name='privacy'),

    # FAQs
    # /faqs/
    path('faqs/', old_views.faqs, name='faqs'),
]

# Donate / Donations
urlpatterns += [
    # Donation
    # /donate/
    path('donate/', old_views.donate, name='donate'),

    # /donate/cancel/
    path('donate/cancel/', old_views.donate_cancel, name='donate_cancel'),

    # /donate/return/
    path('donate/return/', old_views.donate_return, name='donate_return'),

    # /donate/paypal/
    path('donate/paypal/', include('paypal.standard.ipn.urls')),

    # One off pages
    # /zirmed/
    path('zirmed/', old_views.donate, name='donate_zirmed'),
]


# All Auth / Logins
urlpatterns += [

    # AllAuth
    # /accounts/
    path('accounts/', include('allauth.urls')),
]

# Login As
urlpatterns += [
    path('dj-admin/', include('loginas.urls')),
]

# Admin
urlpatterns += [

    # Django Admin
    # /dj-admin/
    path('dj-admin/', admin.site.urls),

    # Admin
    # /admin/
    path('admin/', old_views.cdc_admin, name='cdc_admin'),


    # Admin Classes
    # /admin/class/ID/stats/
    path('admin/class/<int:pk>/stats/', old_views.session_stats, name='stats'),

    # /admin/class/ID/check-in/
    path('admin/class/<int:pk>/check-in/', old_views.session_check_in, name='check_in'),

    # /admin/class/ID/donations/
    path('admin/class/<int:pk>/donations/', old_views.session_donations, name='donations'),

    # /admin/class/ID/check-in-mentors/
    path(
        'admin/class/<int:pk>/check-in-mentors/',
        old_views.session_check_in_mentors,
        name='check_in_mentors'
    ),


    # Admin Meetings
    # /admin/meeting/ID/check-in/
    path('admin/meeting/<int:meeting_id>/check-in/', old_views.meeting_check_in, name='meeting-check-in'),


    # Admin Check System
    # /admin/checksystem/
    path('admin/checksystem/', old_views.check_system, name='check_system'),
]

# Sessions
urlpatterns += [
    # Classes
    # /classes/
    path('classes/', SessionsView.as_view(), name='sessions'),
    path('class/', SessionsRedirectView.as_view()),

    # Individual Class
    # /class/ID/
    path('class/<int:pk>/', SessionDetailView.as_view(), name='session-detail'),

    # Redirect
    # /c/ID/ -> /class/ID/
    path('c/<int:pk>/', SessionDetailRedirectView.as_view()),

    # Redirect
    # /class/YYYY/MM/DD/SLUG/ID/ -> /class/ID/
    path('class/<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/', SessionDetailRedirectView.as_view()),



    # Password
    path('class/<int:pk>/password/', PasswordSessionView.as_view(), name='session-password'),

    # Redirect
    # /class/YYYY/MM/DD/SLUG/ID/password/ -> /class/ID/password/
    path(
        'class/<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/password/',
        PasswordSessionRedirectView.as_view()
    ),



    # Announce
    # /class/ID/announce/mentors
    path('class/<int:pk>/announce/mentors/', old_views.session_announce_mentors, name='session-announce-mentors'),

    # /class/ID/announce/guardians
    path('class/<int:pk>/announce/guardians/', old_views.session_announce_guardians, name='session-announce-guardians'),



    # Calendar
    # /class/ID/calendar/
    path('class/<int:pk>/calendar/', SessionCalendarView.as_view(), name='session-calendar'),

    # /class/YYYY/MM/DD/SLUG/ID/calendar/ -> /class/ID/calendar/
    path(
        'class/<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/calendar/',
        SessionCalendarRedirectView.as_view()
    ),



    # Sign up
    # /class/ID/sign-up/
    path('class/<int:pk>/sign-up/', SessionSignUpView.as_view(), name='session-sign-up'),

    # /class/YYYY/MM/DD/SLUG/ID/sign-up/ -> /class/ID/sign-up/
    path('class/<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/sign-up/', SessionSignUpRedirectView.as_view()),

    # /class/ID/sign-up/STUDENT-ID/
    path('class/<int:pk>/sign-up/<int:student_id>/', SessionSignUpView.as_view(), name='session-sign-up'),

    # /class/YYYY/MM/DD/SLUG/ID/sign-up/STUDENT-ID/ -> /class/ID/sign-up/STUDENT-ID/
    path(
        'class/<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/sign-up/<int:student_id>/',
        SessionSignUpRedirectView.as_view(),
    ),

]

# Mentors
urlpatterns += [
    # Mentors
    # /mentors/
    path('mentors/', old_views.mentors, name='mentors'),

    # /mentor/ID/
    path('mentor/<int:pk>/', old_views.mentor_detail, name='mentor-detail'),

    # 301 /mentors/ID/
    path('mentors/<int:pk>/', RedirectView.as_view(pattern_name='mentor-detail')),

    # /mentor/ID/reject-avatar/
    path('mentor/<int:pk>/reject-avatar/', old_views.mentor_reject_avatar, name='mentor-reject-avatar'),

    # 301 /mentors/ID/reject-avatar/
    path('mentors/<int:pk>/reject-avatar/', RedirectView.as_view(pattern_name='mentor-reject-avatar')),

    # /mentor/ID/approve-avatar/
    path('mentor/<int:pk>/approve-avatar/', old_views.mentor_approve_avatar, name='mentor-approve-avatar'),

    # 301 /mentors/ID/approve-avatar/
    path('mentors/<int:pk>/approve-avatar/', RedirectView.as_view(pattern_name='mentor-approve-avatar')),
]

# Students
urlpatterns += [
    # Student
    # /student/ID/
    path('student/<int:student_id>/', old_views.student_detail, name='student-detail'),
]

# Dojo
urlpatterns += [

    # Dojo / Account
    # /dojo/
    path('dojo/', old_views.dojo, name='dojo'),

    # Welcome
    # /welcome/
    path('welcome/', WelcomeView.as_view(), name='welcome'),
]

# Meetings
urlpatterns += [
    # Meetings
    # /meetings/
    path('meetings/', MeetingsView.as_view(), name='meetings'),

    # Individual Meeting
    # /meeting/ID/
    path('meeting/<int:pk>/', MeetingDetailView.as_view(), name='meeting-detail'),

    # Redirect /m/ID/ -> /meeting/ID/
    path('m/<int:pk>/', MeetingDetailRedirectView.as_view()),

    # Redirect /meeting/YYYY/MM/DD/SLUG/ID/ -> /meeting/ID/
    path('meeting/<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/', MeetingDetailRedirectView.as_view()),


    # /meeting/ID/announce/
    path('meeting/<int:pk>/announce/', meeting_announce, name='meeting-announce'),


    # Meeting sign up
    # /meeting/ID/sign-up/
    path('meeting/<int:pk>/register/', meeting_sign_up, name='meeting-register'),

    # Meeting Calendar
    # /meeting/ID/calendar/
    path('meeting/<int:pk>/calendar/', MeetingCalendarView.as_view(), name='meeting-calendar'),
]


# robots.txt
urlpatterns += [
    path('robots.txt', lambda r: HttpResponse('User-agent: *\nDisallow:', content_type='text/plain'))
]

# favicon.ico
urlpatterns += [
    path(
        'favicon.ico',
        RedirectView.as_view(url=staticfiles_storage.url('favicon.ico'), permanent=False),
        name='favicon'
    ),
]

# Static files
urlpatterns += static(
    settings.STATIC_URL,
    document_root=settings.STATIC_ROOT
)

# Media files
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)

# Anymail
urlpatterns += [
    path('anymail/', include('anymail.urls')),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            '400/',
            defaults.bad_request,
            kwargs={'exception': Exception('Bad Request!')},
        ),
        path(
            '403/',
            defaults.permission_denied,
            kwargs={'exception': Exception('Permission Denied')},
        ),
        path(
            '404/',
            defaults.page_not_found,
            kwargs={'exception': Exception('Page not Found')},
        ),
        path('500/', defaults.server_error),
    ]

    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
