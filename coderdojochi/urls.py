from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views

from coderdojochi.views import RegisterView

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'coderdojochi.views.home', name='home'),
    url(r'^faqs/$', 'coderdojochi.views.faqs', name='faqs'),
    url(r'^donate/$','coderdojochi.views.donate',name='donate'),
    url(r'^donate/cancel/$','coderdojochi.views.donate_cancel', name='donate_cancel'),
    url(r'^donate/return/$','coderdojochi.views.donate_return', name='donate_return'),
    url(r'^donate/paypal/$', include('paypal.standard.ipn.urls')),
    url(r'^about/$','coderdojochi.views.about',name='about'),
    url(r'^privacy/$','coderdojochi.views.privacy',name='privacy'),
    url(r'^volunteer/$', 'coderdojochi.views.volunteer', name='volunteer'),
    url(r'^contact/', 'coderdojochi.views.contact', name='contact'),

    url(r'^register/$', RegisterView.as_view(), name='register'),
    url(r'^accounts/register/$', RegisterView.as_view(), name='register'),
    url(r'^register/enroll/$', RegisterView.as_view(enroll=True), name='register_enroll'),

    url(r'^mentors/(?P<mentor_id>[\d]+)/reject-avatar/$', 'coderdojochi.views.mentor_reject_avatar', name='mentor_reject_avatar'),
    url(r'^mentors/(?P<mentor_id>[\d]+)/approve-avatar/$', 'coderdojochi.views.mentor_approve_avatar', name='mentor_approve_avatar'),
    url(r'^mentors/(?P<mentor_id>[\d]+)/$', 'coderdojochi.views.mentor_detail', name='mentor_detail'),
    url(r'^mentors/$', 'coderdojochi.views.mentors', name='mentors'),

    url(r'^student/(?P<student_id>[\d]+)/$', 'coderdojochi.views.student_detail', name='student_detail'),

    url(r'^classes/(?P<year>[\d]+)/(?P<month>[\d]+)/$', 'coderdojochi.views.sessions', name='sessions'),
    url(r'^classes/$', 'coderdojochi.views.sessions', name='sessions'),
    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/sign-up/(?P<student_id>[\d]+)/$', 'coderdojochi.views.session_sign_up', name='session_sign_up'),
    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/sign-up/$', 'coderdojochi.views.session_sign_up', name='session_sign_up'),
    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/enroll/$', 'coderdojochi.views.session_detail_enroll', name='session_detail_enroll'),
    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)/calendar/$', 'coderdojochi.views.session_ics', name='session_ics'),
    url(r'^class/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<slug>[-\w]+)/(?P<session_id>[\d]+)$', 'coderdojochi.views.session_detail', name='session_detail'),
    url(r'^class/(?P<session_id>[\d]+)/announce/$', 'coderdojochi.views.session_announce', name='session_announce'),

    url(r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<meeting_id>[\d]+)/sign-up/$', 'coderdojochi.views.meeting_sign_up', name='meeting_sign_up'),
    url(r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<meeting_id>[\d]+)/calendar/$', 'coderdojochi.views.meeting_ics', name='meeting_ics'),
    url(r'^meeting/(?P<year>[\d]+)/(?P<month>[\d]+)/(?P<day>[\d]+)/(?P<meeting_id>[\d]+)$', 'coderdojochi.views.meeting_detail', name='meeting_detail'),
    url(r'^meeting/(?P<meeting_id>[\d]+)/announce/$', 'coderdojochi.views.meeting_announce', name='meeting_announce'),

    url(r'^admin/class/(?P<session_id>[\d]+)/stats/$', 'coderdojochi.views.session_stats', name='stats'),
    url(r'^admin/class/(?P<session_id>[\d]+)/check-in/$', 'coderdojochi.views.session_check_in', name='check_in'),
    url(r'^admin/class/(?P<session_id>[\d]+)/check-in-mentors/$', 'coderdojochi.views.session_check_in_mentors', name='check_in_mentors'),
    url(r'^admin/', 'coderdojochi.views.cdc_admin', name='cdc_admin'),

    url(r'^welcome/$', 'coderdojochi.views.welcome', name='welcome'),
    url(r'^dojo/$', 'coderdojochi.views.dojo', name='dojo'),

    #override the default urls
    url(r'^password/change/$', auth_views.password_change, name='password_change'),
    url(r'^password/change/done/$', auth_views.password_change_done, name='password_change_done'),
    url(r'^password/reset/$', auth_views.password_reset, name='password_reset'),
    url(r'^password/reset/done/$', auth_views.password_reset_done, name='password_reset_done'),
    url(r'^password/reset/complete/$', auth_views.password_reset_complete, name='password_reset_complete'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', auth_views.password_reset_confirm, name='password_reset_confirm'),

    url(r'^login/$', auth_views.login, {'template_name': 'registration/login.html'}),
    url(r'^login/user/(?P<user_id>.+)/$', 'loginas.views.user_login', name='loginas-user-login'),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'', include('social_auth.urls')),
    url(r'^dj-admin/', include(admin.site.urls)),
    url(r'^avatar/', include('avatar.urls')),
)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
