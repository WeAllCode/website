# -*- coding: utf-8 -*-

from loginas import views as loginas_views

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as django_views
from django.views.generic import RedirectView

from . import old_views as coderdojochi_views

from .views.profile import DojoMentorView
from .views.volunteer import VolunteerView
from .views.general import HomeView, WelcomeView, AboutView
from .views.sessions import (
    SessionsView, SessionDetailView, SessionSignUpView, SessionIcsView,
    PasswordSessionView
)
from .views.meetings import MeetingsView, MeetingDetailView, MeetingIcsView

admin.autodiscover()

urlpatterns = [
    # /
    url(
        r'^$',
        # coderdojochi_views.home,
        HomeView.as_view(),
        name='home',
    ),


    # FAQs
    # /faqs/
    url(
        r'^faqs/$',
        coderdojochi_views.faqs,
        name='faqs',
    ),


    # Donation
    # /donate/
    url(
        r'^donate/$',
        coderdojochi_views.donate,
        name='donate',
    ),
    # /zirmed/
    url(
        r'^zirmed/$',
        coderdojochi_views.donate,
        name='donate_zirmed',
    ),
    # /donate/cancel/
    url(
        r'^donate/cancel/$',
        coderdojochi_views.donate_cancel,
        name='donate_cancel',
    ),
    # /donate/return/
    url(
        r'^donate/return/$',
        coderdojochi_views.donate_return,
        name='donate_return',
    ),
    # /donate/paypal/
    url(
        r'^donate/paypal/',
        include('paypal.standard.ipn.urls')
    ),


    # About
    # /about/
    url(
        r'^about/$',
        AboutView.as_view(),
        name='about',
    ),

    # Privacy
    # /privary/
    url(
        r'^privacy/$',
        coderdojochi_views.privacy,
        name='privacy',
    ),


    # Volunteer
    # /volunteer/
    url(
        r'^volunteer/',
        VolunteerView.as_view(),
        name='volunteer',
    ),


    # Contact
    # /contact/
    url(
        r'^contact/',
        coderdojochi_views.contact,
        name='contact',
    ),


    # Mentors
    # /mentors/
    url(
        r'^mentors/$',
        coderdojochi_views.mentors,
        name='mentors',
    ),
    # /mentor/ID/
    url(
        r'^mentor/(?P<mentor_id>[\d]+)/$',
        coderdojochi_views.mentor_detail,
        name='mentor_detail',
    ),
    # 301 /mentors/ID/
    url(
        r'^mentors/(?P<mentor_id>[\d]+)/$',
        RedirectView.as_view(pattern_name='mentor_detail'),
    ),

    # /mentor/ID/reject-avatar/
    url(
        r'^mentor/(?P<mentor_id>[\d]+)/reject-avatar/$',
        coderdojochi_views.mentor_reject_avatar,
        name='mentor_reject_avatar',
    ),
    # 301 /mentors/ID/reject-avatar/
    url(
        r'^mentors/(?P<mentor_id>[\d]+)/reject-avatar/$',
        RedirectView.as_view(pattern_name='mentor_reject_avatar'),
    ),

    # /mentor/ID/approve-avatar/
    url(
        r'^mentor/(?P<mentor_id>[\d]+)/approve-avatar/$',
        coderdojochi_views.mentor_approve_avatar,
        name='mentor_approve_avatar',
    ),
    # 301 /mentors/ID/approve-avatar/
    url(
        r'^mentors/(?P<mentor_id>[\d]+)/approve-avatar/$',
        RedirectView.as_view(pattern_name='mentor_approve_avatar'),
    ),


    # Student
    # /student/ID/
    url(
        r'^student/(?P<student_id>[\d]+)/$',
        coderdojochi_views.student_detail,
        name='student_detail',
    ),

    # Classes
    # /classes/
    url(
        r'^classes/$',
        # coderdojochi_views.sessions,
        SessionsView.as_view(),
        name='sessions',
    ),
    # /classes/YYYY/MM/
    url(
        r'^classes/(?P<year>[\d]+)/(?P<month>[\d]+)/$',
        # coderdojochi_views.sessions,
        SessionsView.as_view(),
        name='sessions',
    ),


    # Individual Class
    # /c/ID/
    url(
        r'^c/(?P<session_id>[\d]+)/$',
        # coderdojochi_views.session_detail_short,
        SessionDetailView.as_view(),
        name='session_detail_short',
    ),
    # /class/ID/
    url(
        r'^class/(?P<session_id>[\d]+)/$',
        # coderdojochi_views.session_detail_short,
        SessionDetailView.as_view(),
        name='session_detail_short',
    ),
    # /class/ID/announce/mentors
    url(
        r'^class/(?P<session_id>[\d]+)/announce/mentors/$',
        coderdojochi_views.session_announce_mentors,
        name='session_announce_mentors',
    ),
    # /class/ID/announce/guardians
    url(
        r'^class/(?P<session_id>[\d]+)/announce/guardians/$',
        coderdojochi_views.session_announce_guardians,
        name='session_announce_guardians',
    ),
    # /class/YYYY/MM/DD/SLUG/ID/
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/$',
        # coderdojochi_views.session_detail,
        SessionDetailView.as_view(),
        name='session_detail',
    ),
    # /class/YYYY/MM/DD/SLUG/ID/password
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/password/$',
        PasswordSessionView.as_view(),
        name='session_password',
    ),
    # /class/YYYY/MM/DD/SLUG/ID/calendar/
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/calendar/$',
        # coderdojochi_views.session_ics,
        SessionIcsView.as_view(),
        name='session_ics',
    ),
    # /class/YYYY/MM/DD/SLUG/ID/sign-up/
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/sign-up/$',
        # coderdojochi_views.session_sign_up,
        SessionSignUpView.as_view(),
        name='session_sign_up',
    ),
    # /class/YYYY/MM/DD/SLUG/ID/sign-up/STUDENT-ID
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/sign-up'
        r'/(?P<student_id>[\d]+)/$',
        # coderdojochi_views.session_sign_up,
        SessionSignUpView.as_view(),
        name='session_sign_up',
    ),
    # /class/YYYY/MM/DD/SLUG/ID/enroll/
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/enroll/$',
        # coderdojochi_views.session_detail_enroll,
        SessionDetailView.as_view(),
        name='session_detail_enroll',
    ),


    # Meetings
    # /meetings/
    url(
        r'^meetings/$',
        # coderdojochi_views.meetings,
        MeetingsView.as_view(),
        name='meetings',
    ),

    # Individual Meeting
    # /m/ID/
    url(
        r'^m/(?P<meeting_id>[\d]+)/$',
        # coderdojochi_views.meeting_detail_short,
        MeetingDetailView.as_view(),
        name='meeting_detail_short',
    ),
    # /meeting/ID/
    url(
        r'^meeting/(?P<meeting_id>[\d]+)/$',
        # coderdojochi_views.meeting_detail_short,
        MeetingDetailView.as_view(),
        name='meeting_detail_short',
    ),
    # /meeting/ID/announce/
    url(
        r'^meeting/(?P<meeting_id>[\d]+)/announce/$',
        coderdojochi_views.meeting_announce,
        name='meeting_announce',
    ),
    # /meeting/YYYY/MM/DD/SLUG/ID/
    url(
        r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<meeting_id>[\d]+)/$',
        # coderdojochi_views.meeting_detail,
        MeetingDetailView.as_view(),
        name='meeting_detail',
    ),
    # /meeting/YYYY/MM/DD/SLUG/ID/sign-up/
    url(
        r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<meeting_id>[\d]+)/sign-up/$',
        coderdojochi_views.meeting_sign_up,
        name='meeting_sign_up',
    ),
    # /meeting/YYYY/MM/DD/SLUG/ID/calendar/
    url(
        r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<meeting_id>[\d]+)/calendar/$',
        # coderdojochi_views.meeting_ics,
        MeetingIcsView.as_view(),
        name='meeting_ics',
    ),


    # Admin
    # /admin/
    url(
        r'^admin/$',
        coderdojochi_views.cdc_admin,
        name='cdc_admin',
    ),

    # Admin Classes
    # /admin/class/ID/stats/
    url(
        r'^admin/class/(?P<session_id>[\d]+)/stats/$',
        coderdojochi_views.session_stats,
        name='stats',
    ),
    # /admin/class/ID/check-in/
    url(
        r'^admin/class/(?P<session_id>[\d]+)/check-in/$',
        coderdojochi_views.session_check_in,
        name='check_in',
    ),
    # /admin/class/ID/donations/
    url(
        r'^admin/class/(?P<session_id>[\d]+)/donations/$',
        coderdojochi_views.session_donations,
        name='donations'
    ),
    # /admin/class/ID/check-in-mentors/
    url(
        r'^admin/class/(?P<session_id>[\d]+)/check-in-mentors/$',
        coderdojochi_views.session_check_in_mentors,
        name='check_in_mentors',
    ),


    # Admin Meetings
    # /admin/meeting/ID/check-in/
    url(
        r'^admin/meeting/(?P<meeting_id>[\d]+)/check-in/$',
        coderdojochi_views.meeting_check_in,
        name='meeting_check_in',
    ),


    # Admin Check System
    # /admin/checksystem/
    url(
        r'^admin/checksystem/$',
        coderdojochi_views.check_system,
        name='check_system',
    ),


    # Welcome
    # /welcome/
    url(
        r'^welcome/$',
        # coderdojochi_views.welcome,
        WelcomeView.as_view(),
        name='welcome',
    ),


    # Dojo / Account
    # /dojo/
    url(
        r'^dojo/$',
        coderdojochi_views.dojo,
        name='dojo',
    ),


    # Login as user
    # /login/user/ID/
    url(
        r'^login/user/(?P<user_id>.+)/$',
        loginas_views.user_login,
        name='loginas-user-login',
    ),

    # Account logout override
    # /accounts/logout/
    url(
        r'^accounts/logout/$',
        django_views.logout,
        {
            'next_page': '/'
        },
        name='account_logout',
    ),

    # AllAuth
    # /accounts/
    url(
        r'^accounts/',
        include('allauth.urls'),
    ),

    # Django Admin
    # /dj-admin/
    url(
        r'^dj-admin/',
        include(admin.site.urls),
    ),
]

urlpatterns += static(
    settings.STATIC_URL,
    document_root=settings.STATIC_ROOT
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(
        url(
            r'^__debug__/',
            include(debug_toolbar.urls)
        ),
    )
