# from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView

from coderdojochi.models import Mentor


class AdminMentorAvatarApproveRedirectView(RedirectView):

    url = '/dj-admin/'
    # pattern_name = reverse_lazy('home')

    def get_redirect_url(self, *args, **kwargs):
        mentor = get_object_or_404(Mentor, pk=kwargs['pk'])
        mentor.avatar_approved = True
        mentor.save()
        return super(AdminMentorAvatarApproveRedirectView, self).get_redirect_url(*args, **kwargs)
