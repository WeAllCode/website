from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as django_views
from django.http import HttpResponse
from django.urls import path
from django.views import defaults
from django.views.generic import RedirectView
from loginas import views as loginas_views

from . import old_views
from .views.general import AboutView, HomeView, PrivacyView, WelcomeView
from .views.meetings import (MeetingCalendarRedirectView, MeetingCalendarView,
                             MeetingDetailRedirectView, MeetingDetailView,
                             MeetingsView, meeting_announce, meeting_sign_up)
from .views.profile import DojoMentorView
from .views.sessions import (PasswordSessionRedirectView, PasswordSessionView,
                             SessionCalendarRedirectView, SessionCalendarView,
                             SessionDetailRedirectView, SessionDetailView,
                             SessionSignUpRedirectView, SessionSignUpView,
                             SessionsRedirectView, SessionsView)
from .views.volunteer import VolunteerView

admin.autodiscover()

# Empty to start
urlpatterns = []

# General Pages
urlpatterns += [
    path('', include('weallcode.urls')),
]

# Accounts
urlpatterns += [
    path('account/', include('accounts.urls')),
]

# Payments
urlpatterns += [path('donate/', include('payments.urls'))]

# Old General
urlpatterns += [

    path('old/', include([
        # Home
        path('', HomeView.as_view(), name='home'),

        # About
        path('about/', AboutView.as_view(), name='about'),

        # Volunteer
        path('volunteer/', VolunteerView.as_view(), name='volunteer'),

        # Contact
        path('contact/', old_views.contact, name='contact'),

        # Privacy
        path('privacy/', PrivacyView.as_view(), name='privacy'),

        # FAQs
        path('faqs/', old_views.faqs, name='faqs'),


        # Meetings
        path('meetings/', include([
            # Meetings
            # /meetings/
            path('', MeetingsView.as_view(), name='meetings'),

            # Individual Meeting
            # /meeting/ID/
            path('<int:pk>/', MeetingDetailView.as_view(), name='meeting-detail'),

            # /meeting/ID/announce/
            path('<int:pk>/announce/', meeting_announce, name='meeting-announce'),

            # Meeting sign up
            # /meeting/ID/sign-up/
            path('<int:pk>/register/', meeting_sign_up, name='meeting-register'),

            # Meeting Calendar
            # /meeting/ID/calendar/
            path('<int:pk>/calendar/', MeetingCalendarView.as_view(), name='meeting-calendar'),
        ])),

        # FIXME: Old redirects. Remove by July 2018
        # Redirect /m/ID/ -> /meeting/ID/
        path('m/<int:pk>/', MeetingDetailRedirectView.as_view()),

        # FIXME: Old redirects. Remove by July 2018
        path('meeting/', include([
            # Redirect /meeting/ID/ -> /meetings/ID/
            path('<int:pk>/', MeetingDetailRedirectView.as_view()),

            # Redirect /meeting/YYYY/MM/DD/SLUG/ID/ -> /meeting/ID/
            path('<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/', MeetingDetailRedirectView.as_view()),

            # Redirect /meeting/ID/calendar/ -> /classes/ID/calendar/
            path('<int:pk>/calendar/', MeetingCalendarRedirectView.as_view()),
        ])),

    ])),

]

# Login As
urlpatterns += [
    path('dj-admin/', include('loginas.urls')),
]

# Django Admin
urlpatterns += [
    # /dj-admin/
    path('dj-admin/', admin.site.urls),
]

# Admin
urlpatterns += [
    path('admin/', include([
        # Admin
        # /admin/
        path('', old_views.cdc_admin, name='cdc-admin'),

        path('classes/', include([
            # /admin/classes/ID/stats/
            path('<int:pk>/stats/', old_views.session_stats, name='stats'),

            # /admin/classes/ID/check-in/
            path('<int:pk>/check-in/', old_views.session_check_in,
                 name='student-check-in'),

            # /admin/classes/ID/check-in-mentors/
            path('<int:pk>/check-in-mentors/',
                 old_views.session_check_in_mentors, name='mentor-check-in'),

            # /admin/classes/ID/donations/
            path('<int:pk>/donations/',
                 old_views.session_donations, name='donations'),
        ])),

        path('meetings/', include([
            # /admin/meeting/ID/check-in/
            path('<int:meeting_id>/check-in/',
                 old_views.meeting_check_in, name='meeting-check-in'),
        ])),

        # Admin Check System
        # /admin/checksystem/
        path('checksystem/', old_views.check_system, name='check-system'),
    ]))
]

# Sessions
urlpatterns += [

    path('classes/', include([
        # Classes
        # /classes/
        path('', SessionsView.as_view(), name='sessions'),

        # Individual Class
        # /classes/ID/
        path('<int:pk>/', SessionDetailView.as_view(), name='session-detail'),

        # Password
        # /classes/ID/password/
        path('<int:pk>/password/', PasswordSessionView.as_view(),
             name='session-password'),

        # Announce
        # /classes/ID/announce/mentors/
        path('<int:pk>/announce/mentors/', old_views.session_announce_mentors,
             name='session-announce-mentors'),

        # /classes/ID/announce/guardians/
        path('<int:pk>/announce/guardians/', old_views.session_announce_guardians,
             name='session-announce-guardians'),

        # Calendar
        # /classes/ID/calendar/
        path('<int:pk>/calendar/', SessionCalendarView.as_view(),
             name='session-calendar'),

        # Sign up
        # /classes/ID/sign-up/
        path('<int:pk>/sign-up/', SessionSignUpView.as_view(),
             name='session-sign-up'),

        # /classes/ID/sign-up/STUDENT-ID/
        path('<int:pk>/sign-up/<int:student_id>/',
             SessionSignUpView.as_view(), name='session-sign-up'),
    ])),

    # FIXME: Old redirects. Remove by July 2018
    path('class/', include([
        # Redirect /class/ -> /classes/
        path('', SessionsRedirectView.as_view()),

        # Redirect /class/ID/ -> /classes/ID/
        path('<int:pk>/', SessionDetailRedirectView.as_view()),

        # Redirect /class/YYYY/MM/DD/SLUG/ID/ -> /classes/ID/
        path('<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/',
             SessionDetailRedirectView.as_view()),

        # Redirect /class/YYYY/MM/DD/SLUG/ID/password/ -> /classes/ID/password/
        path('<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/password/',
             PasswordSessionRedirectView.as_view()),

        # Redirect /class/YYYY/MM/DD/SLUG/ID/calendar/ -> /classes/ID/calendar/
        path('<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/calendar/',
             SessionCalendarRedirectView.as_view()),

        # Redirect /class/YYYY/MM/DD/SLUG/ID/sign-up/ -> /classes/ID/sign-up/
        path('<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/sign-up/',
             SessionSignUpRedirectView.as_view()),

        # Redirect /class/YYYY/MM/DD/SLUG/ID/sign-up/STUDENT-ID/ -> /classes/ID/sign-up/STUDENT-ID/
        path(
            '<int:year>/<int:month>/<int:day>/<slug:slug>/<int:pk>/sign-up/<int:student_id>/',
            SessionSignUpRedirectView.as_view(),
        ),

        # Redirect /class/ID/calendar/ -> /classes/ID/calendar/
        path('<int:pk>/calendar/', SessionCalendarRedirectView.as_view()),
    ])),

    # FIXME: Old redirects. Remove by July 2018
    # Redirect /c/ID/ -> /class/ID/
    path('c/<int:pk>/', SessionDetailRedirectView.as_view()),
]

# Mentors
# TODO: Uncomment `app_name` after we move mentors to it's own app.
# app_name = 'mentors'
urlpatterns += [
    path('mentors/', include([
        # Mentors
        # /
        path('', old_views.mentors, name='mentors'),

        # /ID/
        path('<int:pk>/', old_views.mentor_detail, name='mentor-detail'),

        # /ID/reject-avatar/
        path('<int:pk>/reject-avatar/', old_views.mentor_reject_avatar,
             name='mentor-reject-avatar'),

        # /ID/approve-avatar/
        path('<int:pk>/approve-avatar/', old_views.mentor_approve_avatar,
             name='mentor-approve-avatar'),
    ])),

    # FIXME: Old redirects. Remove by July 2018
    # Redirect /mentor/* -> /mentors/*
    path('mentor/', include([
        path('', RedirectView.as_view(pattern_name='mentors')),
        path('<int:pk>/', RedirectView.as_view(pattern_name='mentor-detail')),
        path('<int:pk>/reject-avatar/',
             RedirectView.as_view(pattern_name='mentor-reject-avatar')),
        path('<int:pk>/approve-avatar/',
             RedirectView.as_view(pattern_name='mentor-approve-avatar')),
    ])),
]

# Students
urlpatterns += [
    # Student
    # /student/ID/
    path('students/<int:student_id>/',
         old_views.student_detail, name='student-detail'),
]

# Dojo
urlpatterns += [
    # Dojo / Account
    # /dojo/
    # path('dojo/', old_views.dojo, name='dojo'),

    # Welcome
    # /welcome/
    path('welcome/', WelcomeView.as_view(), name='welcome'),
]

# Meetings
urlpatterns += [

]

# robots.txt
urlpatterns += [
    path('robots.txt', lambda r: HttpResponse(
        'User-agent: *\nDisallow:', content_type='text/plain'))
]

# Anymail
urlpatterns += [
    path('anymail/', include('anymail.urls')),
]

# Media
urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()

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
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls))] + urlpatterns

else:
    from django.contrib.staticfiles.storage import staticfiles_storage
    from django.contrib.staticfiles.views import serve

    # favicon.ico
    favicons = [
        'favicon.ico',
        'android-chrome-192x192.png',
        'android-chrome-256x256.png',
        'apple-touch-icon.png',
        'browserconfig.xml',
        'favicon-16x16.png',
        'favicon-32x32.png',
        'mstile-70x70.png',
        'mstile-150x150.png',
        'mstile-310x150.png',
        'mstile-310x310.png',
        'safari-pinned-tab.svg',
        'site.webmanifest',
    ]

    for favicon in favicons:
        urlpatterns += [
            path(
                favicon,
                RedirectView.as_view(
                    url=staticfiles_storage.url(favicon), permanent=False),
                name=favicon
            ),
        ]

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
