import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.views.generic import DetailView, TemplateView, View
from django.views.generic.base import RedirectView

import arrow

from coderdojochi.mixins import RoleRedirectMixin, RoleTemplateMixin
from coderdojochi.models import Guardian, Mentor, MentorOrder, Order, PartnerPasswordAccess, Session, Student, guardian
from coderdojochi.util import email

from . import guardian, mentor, public
from .calendar import CalendarView

logger = logging.getLogger(__name__)

# this will assign User to our custom CDCUser
User = get_user_model()


def session_confirm_mentor(request, session_obj, order):
    merge_global_data = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "class_code": session_obj.course.code,
        "class_title": session_obj.course.title,
        "class_description": session_obj.course.description,
        "class_start_date": arrow.get(session_obj.mentor_start_date).to("local").format("dddd, MMMM D, YYYY"),
        "class_start_time": arrow.get(session_obj.mentor_start_date).to("local").format("h:mma"),
        "class_end_date": arrow.get(session_obj.mentor_end_date).to("local").format("dddd, MMMM D, YYYY"),
        "class_end_time": arrow.get(session_obj.mentor_end_date).to("local").format("h:mma"),
        "class_location_name": session_obj.location.name,
        "class_location_address": session_obj.location.address,
        "class_location_city": session_obj.location.city,
        "class_location_state": session_obj.location.state,
        "class_location_zip": session_obj.location.zip,
        "class_additional_info": session_obj.additional_info,
        "class_url": f"{settings.SITE_URL}{session_obj.get_absolute_url()}",
        "class_calendar_url": f"{settings.SITE_URL}{session_obj.get_calendar_url()}",
        "microdata_start_date": arrow.get(session_obj.mentor_start_date).to("local").isoformat(),
        "microdata_end_date": arrow.get(session_obj.mentor_end_date).to("local").isoformat(),
        "order_id": order.id,
        "online_video_link": session_obj.online_video_link,
        "online_video_description": session_obj.online_video_description,
    }

    email(
        subject="Mentoring confirmation for {} class".format(
            arrow.get(session_obj.mentor_start_date).to("local").format("MMMM D"),
        ),
        template_name="class-confirm-mentor",
        merge_global_data=merge_global_data,
        recipients=[request.user.email],
        preheader="It's time to use your powers for good.",
    )


def session_confirm_guardian(request, session_obj, order, student):
    merge_global_data = {
        "first_name": request.user.first_name,
        "last_name": request.user.last_name,
        "student_first_name": student.first_name,
        "student_last_name": student.last_name,
        "class_code": session_obj.course.code,
        "class_title": session_obj.course.title,
        "class_description": session_obj.course.description,
        "class_start_date": arrow.get(session_obj.start_date).to("local").format("dddd, MMMM D, YYYY"),
        "class_start_time": arrow.get(session_obj.start_date).to("local").format("h:mma"),
        "class_end_date": arrow.get(session_obj.end_date).to("local").format("dddd, MMMM D, YYYY"),
        "class_end_time": arrow.get(session_obj.end_date).to("local").format("h:mma"),
        "class_location_name": session_obj.location.name,
        "class_location_address": session_obj.location.address,
        "class_location_city": session_obj.location.city,
        "class_location_state": session_obj.location.state,
        "class_location_zip": session_obj.location.zip,
        "class_additional_info": session_obj.additional_info,
        "class_url": session_obj.get_absolute_url(),
        "class_calendar_url": session_obj.get_calendar_url(),
        "microdata_start_date": arrow.get(session_obj.start_date).to("local").isoformat(),
        "microdata_end_date": arrow.get(session_obj.end_date).to("local").isoformat(),
        "order_id": order.id,
        "online_video_link": session_obj.online_video_link,
        "online_video_description": session_obj.online_video_description,
    }

    email(
        subject=f"Upcoming class confirmation for {student.first_name} {student.last_name}",
        template_name="class-confirm-guardian",
        merge_global_data=merge_global_data,
        recipients=[request.user.email],
        preheader="Magical wizards have generated this confirmation. All thanks to the mystical power of coding.",
    )


class SessionDetailView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role == "mentor":
                return mentor.SessionDetailView.as_view()(request, *args, **kwargs)
            else:
                return guardian.SessionDetailView.as_view()(request, *args, **kwargs)
        return public.SessionDetailView.as_view()(request, *args, **kwargs)


# class SessionDetailView(RoleRedirectMixin, RoleTemplateMixin, TemplateView):
#     template_name = "session_detail.html"

#     def dispatch(self, request, *args, **kwargs):
#         session_obj = get_object_or_404(Session, id=kwargs["pk"])

#         if request.method == "GET":
#             if session_obj.password and not self.validate_partner_session_access(self.request, kwargs["pk"]):
#                 return redirect(reverse("session-password", kwargs=kwargs))

#             if request.user.is_authenticated and request.user.role:
#                 if "enroll" in request.GET or "enroll" in kwargs:
#                     return self.enroll_redirect(request, session_obj)

#         # kwargs["session_obj"] = session_obj
#         return super(SessionDetailView, self).dispatch(request, *args, **kwargs)

#     def enroll_redirect(self, request, session_obj):
#         if request.user.role == "mentor":
#             return redirect("session-sign-up", pk=session_obj.id)

#         guardian = get_object_or_404(Guardian, user=request.user)
#         student = get_object_or_404(Student, guardian=guardian, id=(int(request.GET["student"])))

#         if student:
#             return redirect("session-sign-up", pk=session_obj.id, student_id=student.id)

#         return redirect(f"{reverse('welcome')}?next={session_obj.get_absolute_url()}&enroll=True")

#     def validate_partner_session_access(self, request, pk):
#         authed_sessions = request.session.get("authed_partner_sessions")

#         if authed_sessions and pk in authed_sessions:
#             if request.user.is_authenticated:
#                 PartnerPasswordAccess.objects.get_or_create(session_id=pk, user=request.user)
#             return True

#         if request.user.is_authenticated:
#             try:
#                 PartnerPasswordAccess.objects.get(session_id=pk, user_id=request.user.id)
#             except PartnerPasswordAccess.DoesNotExist:
#                 return False
#             else:
#                 return True

#         else:
#             return False

#     def get_context_data(self, **kwargs):
#         print(kwargs["session_obj"].__dict__)
#         context = super(SessionDetailView, self).get_context_data(**kwargs)
#         session_obj = kwargs["session_obj"]
#         context["session"] = session_obj

#         upcoming_classes = Session.objects.filter(is_active=True, start_date__gte=timezone.now()).order_by("start_date")
#         context["upcoming_classes"] = upcoming_classes

#         active_mentors = Mentor.objects.filter(
#             id__in=MentorOrder.objects.filter(session=session_obj, is_active=True).values("mentor__id")
#         )
#         context["active_mentors"] = active_mentors

#         if self.request.user.is_authenticated:
#             if self.request.user.role == "mentor":
#                 account = get_object_or_404(Mentor, user=self.request.user)
#                 session_orders = MentorOrder.objects.filter(session=session_obj, is_active=True,)
#                 context["mentor_signed_up"] = session_orders.filter(mentor=account).exists()

#                 context["spots_remaining"] = session_obj.get_mentor_capacity() - session_orders.count()
#             else:
#                 account = get_object_or_404(Guardian, user=self.request.user)
#                 context["students"] = account.get_students()
#                 context["spots_remaining"] = session_obj.capacity - session_obj.get_active_student_count()
#             context["account"] = account
#         else:
#             context["upcoming_classes"] = upcoming_classes.filter(is_public=True)
#             context["spots_remaining"] = session_obj.capacity - session_obj.objects.get_active_student_count()

#         return context

#     def post(self, request, *args, **kwargs):
#         session_obj = kwargs["session_obj"]
#         if "waitlist" not in request.POST:
#             messages.error(request, "Invalid request, please try again.")
#             return redirect(session_obj.get_absolute_url())

#         if request.POST["waitlist"] == "student":
#             account = Student.objects.get(id=request.POST["account_id"])
#             waitlist_attr = "waitlist_students"
#         else:
#             account = Guardian.objects.get(id=request.POST["account_id"])
#             waitlist_attr = "waitlist_guardians"

#         if request.POST["remove"] == "true":
#             getattr(session_obj, waitlist_attr).remove(account)
#             session_obj.save()
#             messages.success(request, "You have been removed from the waitlist. Thanks for letting us know.")
#         else:
#             getattr(session_obj, waitlist_attr).add(account)
#             session_obj.save()
#             messages.success(request, "Added to waitlist successfully.")
#         return redirect(session_obj.get_absolute_url())


class SessionSignUpView(RoleRedirectMixin, RoleTemplateMixin, TemplateView):
    template_name = "session_sign_up.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):

        session_obj = get_object_or_404(Session, id=kwargs["pk"])
        kwargs["session_obj"] = session_obj

        if request.user.role == "mentor":
            session_orders = MentorOrder.objects.filter(session=session_obj, is_active=True)
            kwargs["mentor"] = get_object_or_404(Mentor, user=request.user)
            kwargs["user_signed_up"] = session_orders.filter(mentor=kwargs["mentor"]).exists()

        elif request.user.role == "guardian":
            kwargs["guardian"] = get_object_or_404(Guardian, user=request.user)
            kwargs["student"] = get_object_or_404(Student, id=kwargs["student_id"])
            kwargs["user_signed_up"] = kwargs["student"].is_registered_for_session(session_obj)

        access_dict = self.check_access(request, *args, **kwargs)

        if access_dict.get("message"):
            if access_dict.get("redirect") == "account_home":
                messages.warning(request, access_dict["message"])
            else:
                messages.error(request, access_dict["message"])

            return redirect(access_dict["redirect"])

        return super(SessionSignUpView, self).dispatch(request, *args, **kwargs)

    def check_access(self, request, *args, **kwargs):

        BG_CHECK_LINK = "https://app.sterlingvolunteers.com/promoorder/3df76c55-9961-46e1-8e5f-f6b38e2ec4dc"

        access_dict = {}
        # Returns a message and redirect url if not working as dict
        if kwargs.get("mentor"):
            if not kwargs["mentor"].background_check:
                access_dict = {
                    "message": (
                        "You cannot sign up for a class until you "
                        f'<a href="{BG_CHECK_LINK}" target="_blank">fill out the background search form</a>.'
                    ),
                    "redirect": request.META.get("HTTP_REFERER", "/dojo"),
                }

        if kwargs.get("student"):
            limits = self.student_limitations(kwargs["student"], kwargs["session_obj"], kwargs["user_signed_up"])
            if limits:
                access_dict = {"message": limits, "redirect": kwargs["session_obj"].get_absolute_url()}
        return access_dict

    def student_limitations(self, student, session_obj, user_signed_up):
        if not student.is_within_gender_limitation(session_obj.gender_limitation):
            return f"Sorry, this class is limited to {session_obj.gender_limitation}s this time around."

        if not student.is_within_age_range(session_obj.minimum_age, session_obj.maximum_age):
            return (
                f"Sorry, this class is limited to students between ages "
                f"{session_obj.minimum_age} and {session_obj.maximum_age}."
            )

        if not user_signed_up and session_obj.capacity <= session_obj.get_active_student_count():
            return "Sorry this class has sold out. Please sign up for the wait list and/or check back later."

        return False

    def get_context_data(self, **kwargs):
        context = super(SessionSignUpView, self).get_context_data(**kwargs)
        context["session"] = kwargs["session_obj"]
        context["user_signed_up"] = kwargs.get("user_signed_up")
        context["student"] = kwargs.get("student")
        return context

    def post(self, request, *args, **kwargs):
        session_obj = kwargs["session_obj"]
        user_signed_up = kwargs["user_signed_up"]
        mentor = kwargs.get("mentor")
        guardian = kwargs.get("guardian")
        student = kwargs.get("student")

        if user_signed_up:
            if mentor:
                order = get_object_or_404(MentorOrder, mentor=mentor, session=session_obj)
            elif student:
                order = get_object_or_404(
                    Order,
                    student=student,
                    session=session_obj,
                    is_active=True,
                )
            order.is_active = False
            order.save()

            messages.success(request, "Thanks for letting us know!")
        else:
            ip = request.META["REMOTE_ADDR"]

            if not settings.DEBUG:
                ip = request.META["HTTP_X_FORWARDED_FOR"] or request.META["REMOTE_ADDR"]

            if mentor:
                order, created = MentorOrder.objects.get_or_create(
                    mentor=mentor,
                    session=session_obj,
                )
            else:
                order, created = Order.objects.get_or_create(
                    guardian=guardian,
                    student=student,
                    session=session_obj,
                )

            order.ip = ip
            order.is_active = True
            order.save()

            messages.success(request, "Success! See you there!")

            if mentor:
                session_confirm_mentor(request, session_obj, order)
            else:
                session_confirm_guardian(request, session_obj, order, student)

        return redirect(session_obj.get_absolute_url())


class PasswordSessionView(TemplateView):
    template_name = "session-partner-password.html"

    def get_context_data(self, **kwargs):
        context = super(PasswordSessionView, self).get_context_data(**kwargs)

        session_obj = get_object_or_404(Session, id=kwargs.get("pk"))

        context["partner_message"] = session_obj.partner_message

        return context

    def post(self, request, *args, **kwargs):
        session_obj = get_object_or_404(Session, id=kwargs.get("pk"))
        password_input = request.POST.get("password")

        context = self.get_context_data(**kwargs)

        if not password_input:
            context["error"] = "Must enter a password."
            return render(request, self.template_name, context)

        if session_obj.password != password_input:
            context["error"] = "Invalid password."
            return render(request, self.template_name, context)

        # Get from user session or create an empty set
        authed_partner_sessions = request.session.get("authed_partner_sessions", [])

        # Add course session id to user session
        authed_partner_sessions.append(kwargs.get("pk"))

        # Remove duplicates
        authed_partner_sessions = list(set(authed_partner_sessions))

        # Store it.
        request.session["authed_partner_sessions"] = authed_partner_sessions

        if request.user.is_authenticated:
            PartnerPasswordAccess.objects.get_or_create(session=session_obj, user=request.user)

        return redirect(session_obj)


class SessionCalendarView(CalendarView):
    event_type = "class"
    event_kwarg = "pk"
    event_class = Session

    def get_summary(self, request, event_obj):
        return f"We All Code: {event_obj.course.code} - {event_obj.course.title}"

    def get_dtstart(self, request, event_obj):
        dtstart = f"{arrow.get(event_obj.start_date).format('YYYYMMDDTHHmmss')}Z"

        if request.user.is_authenticated and request.user.role == "mentor":
            dtstart = f"{arrow.get(event_obj.mentor_start_date).format('YYYYMMDDTHHmmss')}Z"

        return dtstart

    def get_dtend(self, request, event_obj):
        dtend = f"{arrow.get(event_obj.end_date).format('YYYYMMDDTHHmmss')}Z"
        if request.user.is_authenticated and request.user.role == "mentor":
            dtend = f"{arrow.get(event_obj.mentor_end_date).format('YYYYMMDDTHHmmss')}Z"
        return dtend

    def get_description(self, event_obj):
        return strip_tags(event_obj.course.description)

    def get_location(self, request, event_obj):

        # Set default location to the name of the location
        location = f"{event_obj.location.name}"

        # If user has a ticket with us, show online link
        if event_obj.online_video_link and self.request.user.is_authenticated:
            if self.request.user.role == "mentor":
                try:
                    mentor = Mentor.objects.get(user=self.request.user)
                    mentor_signed_up = MentorOrder.objects.filter(
                        session=event_obj, is_active=True, mentor=mentor
                    ).exists()

                    if mentor_signed_up:
                        location = event_obj.online_video_link

                except Mentor.DoesNotExist:
                    pass

            elif self.request.user.role == "guardian":
                try:
                    guardian = Guardian.objects.get(user=self.request.user)
                    students = guardian.get_students()
                    students_signed_up = Order.objects.filter(
                        session=event_obj,
                        is_active=True,
                        student__in=students,
                    ).exists()

                    if students_signed_up:
                        location = event_obj.online_video_link

                except Guardian.DoesNotExist:
                    pass

        elif event_obj.location.address:
            location = (
                f"{event_obj.location.name}, {event_obj.location.address}, "
                f"{event_obj.location.city}, {event_obj.location.state}, {event_obj.location.zip}"
            )

        return location
