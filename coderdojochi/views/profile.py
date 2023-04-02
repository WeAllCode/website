import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from coderdojochi.forms import CDCModelForm, MentorForm
from coderdojochi.models import Mentor, MentorOrder

logger = logging.getLogger(__name__)

# this will assign User to our custom CDCUser
User = get_user_model()


class DojoMentorView(TemplateView):
    template_name = "mentor/dojo.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(DojoMentorView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DojoMentorView, self).get_context_data(**kwargs)
        context["highlight"] = self.request.GET.get("highlight", False)
        mentor = get_object_or_404(Mentor, user=self.request.user)
        context["mentor"] = mentor

        orders = MentorOrder.objects.select_related().filter(
            is_active=True,
            mentor=context["mentor"],
        )

        # upcoming_sessions = orders.filter(is_active=True, session__start_date__gte=timezone.now()).order_by(
        #     "session__start_date"
        # )

        past_sessions = orders.filter(
            is_active=True,
            session__start_date__lte=timezone.now(),
        ).order_by("session__start_date")

        # meeting_orders = MeetingOrder.objects.select_related().filter(mentor=mentor)

        # upcoming_meetings = meeting_orders.filter(
        #     is_active=True,
        #     meeting__is_public=True,
        #     meeting__end_date__gte=timezone.now(),
        # ).order_by("meeting__start_date")

        context["account_complete"] = False

        if (
            mentor.first_name
            and mentor.last_name
            and mentor.avatar
            and mentor.background_check
            and past_sessions.count() > 0
        ):
            context["account_complete"] = True
        return context

    def post(self, request, *args, **kwargs):
        mentor = get_object_or_404(Mentor, user=request.user)

        form = MentorForm(
            request.POST,
            request.FILES,
            instance=mentor,
        )

        user_form = CDCModelForm(
            request.POST,
            request.FILES,
            instance=mentor.user,
        )

        if form.is_valid() and user_form.is_valid():
            form.save()
            user_form.save()
            messages.success(request, "Profile information saved.")

            return redirect("account_home")

        else:
            messages.error(request, "There was an error. Please try again.")
