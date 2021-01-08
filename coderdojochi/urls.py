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
from .views.meetings import (
    MeetingCalendarView,
    MeetingDetailView,
    MeetingsView,
    meeting_announce,
    meeting_sign_up,
)
from .views.mentor import MentorDetailView, MentorListView
from .views.profile import DojoMentorView
from .views.sessions import (
    PasswordSessionView,
    SessionCalendarView,
    SessionDetailView,
    SessionSignUpView
)
from .views.welcome import WelcomeView

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

# Old General
urlpatterns += [

    path('old/', include([

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
            path('<int:pk>/check-in/', old_views.session_check_in, name='student-check-in'),

            # /admin/classes/ID/check-in-mentors/
            path('<int:pk>/check-in-mentors/', old_views.session_check_in_mentors, name='mentor-check-in'),

            # /admin/classes/ID/donations/
            path('<int:pk>/donations/', old_views.session_donations, name='donations'),
        ])),

        path('meetings/', include([
            # /admin/meeting/ID/check-in/
            path('<int:meeting_id>/check-in/', old_views.meeting_check_in, name='meeting-check-in'),
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
        path('', RedirectView.as_view(pattern_name='weallcode-programs'), name='sessions'),

        # Individual Class
        # /classes/ID/
        path('<int:pk>/', SessionDetailView.as_view(), name='session-detail'),

        # Password
        # /classes/ID/password/
        path('<int:pk>/password/', PasswordSessionView.as_view(), name='session-password'),

        # Announce
        # /classes/ID/announce/mentors/
        path('<int:pk>/announce/mentors/', old_views.session_announce_mentors, name='session-announce-mentors'),

        # /classes/ID/announce/guardians/
        path('<int:pk>/announce/guardians/', old_views.session_announce_guardians, name='session-announce-guardians'),

        # Calendar
        # /classes/ID/calendar/
        path('<int:pk>/calendar/', SessionCalendarView.as_view(), name='session-calendar'),

        # Sign up
        # /classes/ID/sign-up/
        path('<int:pk>/sign-up/', SessionSignUpView.as_view(), name='session-sign-up'),

        # /classes/ID/sign-up/STUDENT-ID/
        path('<int:pk>/sign-up/<int:student_id>/', SessionSignUpView.as_view(), name='session-sign-up'),
    ])),

]

# Mentors
# TODO: Uncomment `app_name` after we move mentors to it's own app.
# app_name = 'mentors'
urlpatterns += [
    path('mentors/', include([
        # Mentors
        # /
        path('', MentorListView.as_view(), name='mentors'),

        # /ID/
        path('<int:pk>/', MentorDetailView.as_view(), name='mentor-detail'),

        # /ID/reject-avatar/
        path('<int:pk>/reject-avatar/', old_views.mentor_reject_avatar, name='mentor-reject-avatar'),

        # /ID/approve-avatar/
        path('<int:pk>/approve-avatar/', old_views.mentor_approve_avatar, name='mentor-approve-avatar'),
    ])),

]

# Students
urlpatterns += [
    # Student
    # /student/ID/
    path('students/<int:student_id>/', old_views.student_detail, name='student-detail'),
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
    path('robots.txt', lambda r: HttpResponse('User-agent: *\nDisallow:\nSitemap: ' +
         settings.SITE_URL + '/sitemap.xml', content_type='text/plain'))
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
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
