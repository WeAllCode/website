from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from allauth.account.views import LoginView as AllAuthLoginView
from allauth.account.views import SignupView as AllAuthSignupView
from meta.views import MetadataMixin

from coderdojochi.forms import CDCModelForm, GuardianForm, MentorForm
from coderdojochi.models import Guardian, MeetingOrder, Mentor, MentorOrder, Order, Student


class SignupView(MetadataMixin, AllAuthSignupView):
    template_name = "account/signup.html"
    title = "Sign up | We All Code"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"


class LoginView(MetadataMixin, AllAuthLoginView):
    template_name = "account/login.html"
    title = "Login | We All Code"
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web, game, and app development to "
        "youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_site = "@weallcode"
    twitter_creator = "@weallcode"


@method_decorator(login_required, name="dispatch")
class AccountHomeView(MetadataMixin, TemplateView):
    title = "My Account | We All Code"

    def dispatch(self, *args, **kwargs):
        if not self.request.user.role:
            if "next" in self.request.GET:
                return redirect(f"{reverse('welcome')}?next={self.request.GET['next']}")
            else:
                messages.warning(
                    self.request,
                    "Tell us a little about yourself before going on account.",
                )
            return redirect("welcome")

        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if "highlight" in self.request.GET:
            context["highlight"] = self.request.GET["highlight"]
        else:
            context["highlight"] = False

        context["user"] = self.request.user

        if self.request.user.role == "mentor":
            return {**context, **self.get_context_data_for_mentor()}

        if self.request.user.role == "guardian":
            return {**context, **self.get_context_data_for_guardian()}

        return context

    def get_context_data_for_mentor(self):
        mentor = get_object_or_404(Mentor, user=self.request.user)

        orders = MentorOrder.objects.select_related().filter(
            is_active=True,
            mentor=mentor,
        )

        upcoming_sessions = orders.filter(is_active=True, session__start_date__gte=timezone.now()).order_by(
            "session__start_date"
        )

        past_sessions = orders.filter(is_active=True, session__start_date__lte=timezone.now()).order_by(
            "session__start_date"
        )

        meeting_orders = MeetingOrder.objects.select_related().filter(mentor=mentor)

        upcoming_meetings = meeting_orders.filter(
            is_active=True,
            meeting__is_public=True,
            meeting__end_date__gte=timezone.now(),
        ).order_by("meeting__start_date")

        account_complete = False

        if (
            mentor.first_name
            and mentor.last_name
            and mentor.avatar
            and mentor.background_check
            and past_sessions.count() > 0
        ):
            account_complete = True

        return {
            "mentor": mentor,
            "orders": orders,
            "upcoming_sessions": upcoming_sessions,
            "past_sessions": past_sessions,
            "meeting_orders": meeting_orders,
            "upcoming_meetings": upcoming_meetings,
            "account_complete": account_complete,
        }

    def get_context_data_for_guardian(self):
        guardian = get_object_or_404(Guardian, user=self.request.user)

        students = Student.objects.filter(
            is_active=True,
            guardian=guardian,
        )

        student_orders = Order.objects.filter(
            student__in=students,
        )

        upcoming_orders = student_orders.filter(
            is_active=True,
            session__start_date__gte=timezone.now(),
        ).order_by("session__start_date")

        past_orders = student_orders.filter(
            is_active=True,
            session__start_date__lte=timezone.now(),
        ).order_by("session__start_date")

        return {
            "guardian": guardian,
            "students": students,
            "student_orders": student_orders,
            "upcoming_orders": upcoming_orders,
            "past_orders": past_orders,
        }

    def get(self, *args, **kwargs):
        if self.request.user.role == "mentor":
            return self.get_for_mentor(**kwargs)

        if self.request.user.role == "guardian":
            return self.get_for_guardian(**kwargs)

    def get_for_mentor(self, **kwargs):
        context = self.get_context_data(**kwargs)

        context["form"] = MentorForm(instance=context["mentor"])
        context["user_form"] = CDCModelForm(instance=context["mentor"].user)

        return render(self.request, "account/mentor/home.html", context)

    def get_for_guardian(self, **kwargs):
        context = self.get_context_data(**kwargs)

        context["form"] = GuardianForm(instance=context["guardian"])
        context["user_form"] = CDCModelForm(instance=context["guardian"].user)

        return render(self.request, "account/guardian/home.html", context)

    def post(self, *args, **kwargs):
        if self.request.user.role == "mentor":
            return self.post_for_mentor(**kwargs)

        if self.request.user.role == "guardian":
            return self.post_for_guardian(**kwargs)

    def post_for_mentor(self, **kwargs):
        context = self.get_context_data(**kwargs)

        mentor = context["mentor"]

        form = MentorForm(self.request.POST, self.request.FILES, instance=mentor)

        user_form = CDCModelForm(self.request.POST, self.request.FILES, instance=mentor.user)

        if form.is_valid() and user_form.is_valid():
            form.save()
            user_form.save()
            messages.success(self.request, "Profile information saved.")

            return redirect("account_home")

        else:
            messages.error(self.request, "There was an error. Please try again.")

        context["form"] = form
        context["user_form"] = user_form

        return render(self.request, "account/mentor/home.html", context)

    def post_for_guardian(self, **kwargs):
        context = self.get_context_data(**kwargs)

        guardian = context["guardian"]

        form = GuardianForm(self.request.POST, instance=guardian)

        user_form = CDCModelForm(self.request.POST, instance=guardian.user)

        if form.is_valid() and user_form.is_valid():
            form.save()
            user_form.save()
            messages.success(self.request, "Profile information saved.")

            return redirect("account_home")

        else:
            messages.error(self.request, "There was an error. Please try again.")

        context["form"] = form
        context["user_form"] = user_form

        return render(self.request, "account/guardian/home.html", context)
