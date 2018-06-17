import logging

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from coderdojochi.models import Session


class RoleRedirectMixin(object):
    def dispatch(self, request, *args, **kwargs):
        session_obj = kwargs.get('session_obj')
        user = request.user

        if user.is_authenticated and session_obj and not user.role:
            messages.warning(request, 'Please select one of the following options to continue.')

            next_url = f"{reverse('welcome')}?next={session_obj.get_absolute_url()}"

            if 'enroll' in request.GET:
                next_url += '&enroll=True'

            return redirect(next_url)

        return super(RoleRedirectMixin, self).dispatch(request, *args, **kwargs)
