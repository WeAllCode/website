# -*- coding: utf-8 -*-

from loginas import views as loginas_views

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from . import views as coderdojochi_views


admin.autodiscover()

urlpatterns = [
    url(r'^$', coderdojochi_views.home, name='home'),

    url(r'^faqs/$', coderdojochi_views.faqs, name='faqs'),

    url(r'^donate/$', coderdojochi_views.donate, name='donate'),
    url(r'^donate/cancel/$', coderdojochi_views.donate_cancel, name='donate_cancel'),
    url(r'^donate/return/$', coderdojochi_views.donate_return, name='donate_return'),
    url(r'^donate/paypal/', include('paypal.standard.ipn.urls')),

    url(r'^about/$', coderdojochi_views.about, name='about'),

    url(r'^privacy/$', coderdojochi_views.privacy, name='privacy'),

    url(r'^volunteer/$', coderdojochi_views.volunteer, name='volunteer'),

    url(r'^contact/', coderdojochi_views.contact, name='contact'),

    url(r'^mentors/(?P<mentor_id>[\d]+)/reject-avatar/$', coderdojochi_views.mentor_reject_avatar, name='mentor_reject_avatar'),
    url(r'^mentors/(?P<mentor_id>[\d]+)/approve-avatar/$', coderdojochi_views.mentor_approve_avatar, name='mentor_approve_avatar'),
    url(r'^mentors/(?P<mentor_id>[\d]+)/$', coderdojochi_views.mentor_detail, name='mentor_detail'),
    url(r'^mentors/$', coderdojochi_views.mentors, name='mentors'),

    url(r'^student/(?P<student_id>[\d]+)/$', coderdojochi_views.student_detail, name='student_detail'),

    url(r'^classes/(?P<year>[\d]+)/(?P<month>[\d]+)/$', coderdojochi_views.sessions, name='sessions'),
    url(r'^classes/$', coderdojochi_views.sessions, name='sessions'),

    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/sign-up/(?P<student_id>[\d]+)/$', coderdojochi_views.session_sign_up, name='session_sign_up'),
    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/sign-up/$', coderdojochi_views.session_sign_up, name='session_sign_up'),
    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/enroll/$', coderdojochi_views.session_detail_enroll, name='session_detail_enroll'),
    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/calendar/$', coderdojochi_views.session_ics, name='session_ics'),
    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)$', coderdojochi_views.session_detail, name='session_detail'),
    url(r'^class/(?P<session_id>[\d]+)/announce/$', coderdojochi_views.session_announce, name='session_announce'),

    url(r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<meeting_id>[\d]+)/sign-up/$', coderdojochi_views.meeting_sign_up, name='meeting_sign_up'),
    url(r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<meeting_id>[\d]+)/calendar/$', coderdojochi_views.meeting_ics, name='meeting_ics'),
    url(r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<meeting_id>[\d]+)$', coderdojochi_views.meeting_detail, name='meeting_detail'),
    url(r'^meeting/(?P<meeting_id>[\d]+)/announce/$', coderdojochi_views.meeting_announce, name='meeting_announce'),
    url(r'^admin/class/(?P<meeting_id>[\d]+)/meeting-check-in/$', coderdojochi_views.meeting_check_in, name='meeting_check_in'),

    url(r'^admin/class/(?P<session_id>[\d]+)/stats/$', coderdojochi_views.session_stats, name='stats'),
    url(r'^admin/class/(?P<session_id>[\d]+)/check-in/$', coderdojochi_views.session_check_in, name='check_in'),
    url(r'^admin/class/(?P<session_id>[\d]+)/check-in-mentors/$', coderdojochi_views.session_check_in_mentors, name='check_in_mentors'),

    url(r'^admin/$', coderdojochi_views.cdc_admin, name='cdc_admin'),

    url(r'^admin/dashboard/$', coderdojochi_views.dashboard, name='dashboard'),

    url(r'^welcome/$', coderdojochi_views.welcome, name='welcome'),

    url(r'^dojo/$', coderdojochi_views.dojo, name='dojo'),

    url(r'^login/user/(?P<user_id>.+)/$', loginas_views.user_login, name='loginas-user-login'),

    url(r'^accounts/', include('allauth.urls')),

    url(r'^dj-admin/', include(admin.site.urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
