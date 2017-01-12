# -*- coding: utf-8 -*-

from loginas import views as loginas_views

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as django_views

from . import views as coderdojochi_views


admin.autodiscover()

urlpatterns = [
    url(
        r'^$',
        coderdojochi_views.home,
        name='home',
    ),

    url(
        r'^faqs/$',
        coderdojochi_views.faqs,
        name='faqs',
    ),

    # Donation
    url(
        r'^donate/$',
        coderdojochi_views.donate,
        name='donate',
    ),
    url(
        r'^donate/cancel/$',
        coderdojochi_views.donate_cancel,
        name='donate_cancel',
    ),
    url(
        r'^donate/return/$',
        coderdojochi_views.donate_return,
        name='donate_return',
    ),
    url(
        r'^donate/paypal/', include('paypal.standard.ipn.urls')
    ),

    # About
    url(
        r'^about/$',
        coderdojochi_views.about,
        name='about',
    ),

    # Privacy
    url(
        r'^privacy/$',
        coderdojochi_views.privacy,
        name='privacy',
    ),

    # Volunteer
    url(
        r'^volunteer/$',
        coderdojochi_views.volunteer,
        name='volunteer',
    ),

    # Contact
    url(
        r'^contact/',
        coderdojochi_views.contact,
        name='contact',
    ),

    # Mentors
    url(
        r'^mentors/(?P<mentor_id>[\d]+)/reject-avatar/$',
        coderdojochi_views.mentor_reject_avatar,
        name='mentor_reject_avatar',
    ),
    url(
        r'^mentors/(?P<mentor_id>[\d]+)/approve-avatar/$',
        coderdojochi_views.mentor_approve_avatar,
        name='mentor_approve_avatar',
    ),
    url(
        r'^mentors/(?P<mentor_id>[\d]+)/$',
        coderdojochi_views.mentor_detail,
        name='mentor_detail',
    ),
    url(
        r'^mentors/$',
        coderdojochi_views.mentors,
        name='mentors',
    ),

    # Student
    url(
        r'^student/(?P<student_id>[\d]+)/$',
        coderdojochi_views.student_detail,
        name='student_detail',
    ),

    # Classes
    url(
        r'^classes/(?P<year>[\d]+)/(?P<month>[\d]+)/$',
        coderdojochi_views.sessions,
        name='sessions',
    ),
    url(
        r'^classes/$',
        coderdojochi_views.sessions,
        name='sessions',
    ),

    # Individual Class
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/sign-up'
        r'/(?P<student_id>[\d]+)/$',
        coderdojochi_views.session_sign_up,
        name='session_sign_up',
    ),
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/sign-up/$',
        coderdojochi_views.session_sign_up,
        name='session_sign_up',
    ),
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/enroll/$',
        coderdojochi_views.session_detail_enroll,
        name='session_detail_enroll',
    ),
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/calendar/$',
        coderdojochi_views.session_ics,
        name='session_ics',
    ),
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)$',
        coderdojochi_views.session_detail,
        name='session_detail',
    ),
    url(
        r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/password/$',
        coderdojochi_views.PasswordSessionView.as_view(),
        name='session_password',
    ),
    url(
        r'^class/(?P<session_id>[\d]+)/announce/$',
        coderdojochi_views.session_announce,
        name='session_announce',
    ),

    # Meetings
    url(
        r'^meetings/$',
        coderdojochi_views.meetings,
        name='meetings',
    ),

    # Individual Meeting
    url(
        r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<meeting_id>[\d]+)/sign-up/$',
        coderdojochi_views.meeting_sign_up,
        name='meeting_sign_up',
    ),
    url(
        r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<meeting_id>[\d]+)/calendar/$',
        coderdojochi_views.meeting_ics,
        name='meeting_ics',
    ),
    url(
        r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)'
        r'/(?P<slug>[-\w]+)/(?P<meeting_id>[\d]+)$',
        coderdojochi_views.meeting_detail,
        name='meeting_detail',
    ),
    url(
        r'^meeting/(?P<meeting_id>[\d]+)/announce/$',
        coderdojochi_views.meeting_announce,
        name='meeting_announce',
    ),

    # Admin
    url(
        r'^admin/$',
        coderdojochi_views.cdc_admin,
        name='cdc_admin',
    ),

    # Admin Class
    url(
        r'^admin/class/(?P<session_id>[\d]+)/stats/$',
        coderdojochi_views.session_stats,
        name='stats',
    ),
    url(
        r'^admin/class/(?P<session_id>[\d]+)/check-in/$',
        coderdojochi_views.session_check_in,
        name='check_in',
    ),
    url(
        r'^admin/class/(?P<session_id>[\d]+)/donations/$',
        coderdojochi_views.session_donations,
        name='donations'
    ),
    url(
        r'^admin/class/(?P<session_id>[\d]+)/check-in-mentors/$',
        coderdojochi_views.session_check_in_mentors,
        name='check_in_mentors',
    ),
    url(
        r'^admin/meeting/(?P<meeting_id>[\d]+)/check-in/$',
        coderdojochi_views.meeting_check_in,
        name='meeting_check_in',
    ),

    # Admin Check System
    url(
        r'^admin/checksystem/$',
        coderdojochi_views.check_system,
        name='check_system',
    ),

    # Welcome
    url(
        r'^welcome/$',
        coderdojochi_views.welcome,
        name='welcome',
    ),

    # Dojo / Account
    url(
        r'^dojo/$',
        coderdojochi_views.dojo,
        name='dojo',
    ),

    # Login as user
    url(
        r'^login/user/(?P<user_id>.+)/$',
        loginas_views.user_login,
        name='loginas-user-login',
    ),

    # Account logout override
    url(
        r'^accounts/logout/$',
        django_views.logout,
        {
            'next_page': '/'
        },
        name='account_logout',
    ),

    # AllAuth
    url(
        r'^accounts/',
        include('allauth.urls'),
    ),

    # Django Admin
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
