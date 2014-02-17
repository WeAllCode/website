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

from coderdojochi.models import Class, Mentor, Student
from coderdojochi.forms import MentorForm


# this will assign User to our custom CDCUser
User = get_user_model()


def home(request, template_name="home.html"):

    return render_to_response(template_name,{}, context_instance=RequestContext(request))

@login_required
def dojo(request, template_name="dojo.html"):

    if request.user.role == 'mentor':
        upcoming_classes = Class.objects.filter(mentors=request.user)
        account = Mentor.objects.get(user=request.user)

        if request.method == 'POST':
            form = MentorForm(request.POST, instance=account)
            if form.is_valid():
                form.save()
                messages.add_message(request, messages.SUCCESS, 'Bio saved.')
                return HttpResponseRedirect(reverse('dojo'))
            else:
                messages.add_message(request, messages.ERROR, 'There was an error. Please try again.')
        else:
            form = MentorForm(instance=account)
    else:
        upcoming_classes = Class.objects.filter(students=request.user)
        account = Student.objects.get(user=request.user)
        form = False

    return render_to_response(template_name, {
        'upcoming_classes': upcoming_classes,
        'form': form
    }, context_instance=RequestContext(request))
