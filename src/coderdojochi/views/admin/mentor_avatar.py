# from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView

from coderdojochi.models import Mentor
from coderdojochi.util import email
from django.conf import settings


class AdminMentorAvatarApproveRedirectView(RedirectView):

    url = '/dj-admin/'
    # pattern_name = reverse_lazy('home')

    def get_redirect_url(self, *args, **kwargs):
        mentor = get_object_or_404(Mentor, pk=kwargs['pk'])
        mentor.avatar_approved = True
        mentor.is_public = True
        mentor.save()

        messages.success(
            self.request,
            u'{} {}\'s avatar approved.'.format(
                mentor.user.first_name,
                mentor.user.last_name
            )
        )

        return super(AdminMentorAvatarApproveRedirectView, self).get_redirect_url(*args, **kwargs)


class AdminMentorAvatarRejectRedirectView(RedirectView):

    url = '/dj-admin/'
    # pattern_name = reverse_lazy('home')

    def get_redirect_url(self, *args, **kwargs):
        mentor = get_object_or_404(Mentor, pk=kwargs['pk'])
        mentor.avatar_approved = False
        mentor.is_public = False
        mentor.save()

        email(
            subject='Your CoderDojoChi avatar...',
            template_name='avatar-rejected-mentor',
            context={
                'site_url': settings.SITE_URL,
            },
            recipients=[mentor.user.email],
        )

        messages.warning(
            self.request,
            u'{} {}\'s avatar rejected and their account is no longer public. '
            u'An email notice has been sent to the mentor.'.format(
                mentor.user.first_name,
                mentor.user.last_name
            )
        )

        return super(AdminMentorAvatarRejectRedirectView, self).get_redirect_url(*args, **kwargs)
