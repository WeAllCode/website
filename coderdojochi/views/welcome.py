import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from coderdojochi.forms import GuardianForm, MentorForm, StudentForm
from coderdojochi.models import Guardian, Meeting, Mentor, Session
from coderdojochi.util import email

logger = logging.getLogger(__name__)


class WelcomeView(TemplateView):
    template_name = "welcome.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        next_url = request.GET.get("next")
        kwargs["next_url"] = next_url
        # Check for redirect condition on mentor, otherwise pass as kwarg
        if (
            getattr(request.user, "role", False) == "mentor"
            and request.method == "GET"
        ):
            mentor = get_object_or_404(Mentor, user=request.user)

            if mentor.first_name:
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect("account_home")

            kwargs["mentor"] = mentor
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        mentor = kwargs.get("mentor")
        account = False
        role = getattr(user, "role", False)

        context["role"] = role
        context["next_url"] = kwargs["next_url"]

        if mentor:
            account = mentor
            context["form"] = MentorForm(instance=account)
        if role == "guardian":
            guardian = get_object_or_404(Guardian, user=user)
            account = guardian
            if not account.phone or not account.zip:
                context["form"] = GuardianForm(instance=account)
            else:
                context["add_student"] = True
                context["form"] = StudentForm(
                    initial={"guardian": guardian.pk}
                )

            if account.first_name and account.get_students():
                context["students"] = account.get_students().count()

        context["account"] = account

        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        role = getattr(user, "role", False)
        next_url = kwargs["next_url"]

        if role:
            if role == "mentor":
                account = get_object_or_404(Mentor, user=user)
                return self.update_account(request, account, next_url)
            account = get_object_or_404(Guardian, user=user)

            if not account.phone or not account.zip:
                return self.update_account(request, account, next_url)

            return self.add_student(request, account, next_url)
        else:
            return self.create_new_user(request, user, next_url)

    def update_account(self, request, account, next_url):
        if isinstance(account, Mentor):
            form = MentorForm(request.POST, instance=account)
            role = "mentor"
        else:
            form = GuardianForm(request.POST, instance=account)
            role = "guardian"
        if form.is_valid():
            form.save()
            messages.success(request, "Profile information saved.")
            if next_url:
                if "enroll" in request.GET:
                    next_url = f"{next_url}?enroll=True"
            else:
                if isinstance(account, Mentor):
                    next_url = "account_home"
                else:
                    next_url = "welcome"
            return redirect(next_url)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "role": role,
                "account": account,
                "next_url": next_url,
            },
        )

    def add_student(self, request, account, next_url):
        form = StudentForm(request.POST)
        if form.is_valid():
            new_student = form.save(commit=False)
            new_student.guardian = account
            new_student.save()
            messages.success(request, "Student Registered.")
            if next_url:
                if "enroll" in request.GET:
                    next_url = (
                        f"{next_url}?enroll=True&student={new_student.id}"
                    )
            else:
                next_url = "welcome"
            return redirect(next_url)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "role": "guardian",
                "account": account,
                "next_url": next_url,
                "add_student": True,
            },
        )

    def create_new_user(self, request, user, next_url):
        if request.POST.get("role") == "mentor":
            role = "mentor"
            account, created = Mentor.objects.get_or_create(user=user)
        else:
            role = "guardian"
            account, created = Guardian.objects.get_or_create(user=user)

        account.user.first_name = user.first_name
        account.user.last_name = user.last_name
        account.save()

        user.role = role
        user.save()

        merge_global_data = {
            "user": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

        if next_url:
            next_url = f"?next={next_url}"
        else:
            next_url = None

        if role == "mentor":
            # check for next upcoming meeting
            next_meeting = (
                Meeting.objects.filter(is_active=True, is_public=True)
                .order_by("start_date")
                .first()
            )

            if next_meeting:
                merge_global_data[
                    "next_intro_meeting_url"
                ] = f"{settings.SITE_URL}{next_meeting.get_absolute_url()}"
                merge_global_data[
                    "next_intro_meeting_calendar_url"
                ] = f"{settings.SITE_URL}{next_meeting.get_calendar_url()}"

            if not next_url:
                next_url = reverse("account_home")

            email(
                subject="Welcome!",
                template_name=f"welcome_mentor",
                merge_global_data=merge_global_data,
                recipients=[user.email],
                preheader="Welcome to We All Code! Let's get started..",
            )
        else:
            # check for next upcoming class
            next_class = (
                Session.objects.filter(is_active=True)
                .order_by("start_date")
                .first()
            )

            if next_class:
                merge_global_data[
                    "next_class_url"
                ] = f"{settings.SITE_URL}{next_class.get_absolute_url()}"
                merge_global_data[
                    "next_class_calendar_url"
                ] = f"{settings.SITE_URL}{next_class.get_calendar_url()}"

            if not next_url:
                next_url = reverse("welcome")

            email(
                subject="Welcome!",
                template_name=f"welcome_guardian",
                merge_global_data=merge_global_data,
                recipients=[user.email],
                preheader="Your adventure awaits!",
            )

        return redirect(next_url)
