from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context
from django.template.loader import get_template
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from coderdojochi.models import Class

# this will assign User to our custom CDCUser
User = get_user_model()


def home(request, template_name="home.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

@login_required
def members(request, template_name="members.html"):

    upcoming_classes = Class.objects.filter(mentors=request.user)

    return render_to_response(template_name, {
        'upcoming_classes': upcoming_classes,
    }, context_instance=RequestContext(request))
