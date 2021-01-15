import logging
import operator
from collections import Counter
from datetime import timedelta
from functools import reduce

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, Count, IntegerField, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

import arrow

from coderdojochi.forms import DonationForm, StudentForm
from coderdojochi.models import (
    Donation,
    Equipment,
    EquipmentType,
    Guardian,
    Meeting,
    MeetingOrder,
    Mentor,
    MentorOrder,
    Order,
    Session,
    Student,
)
from coderdojochi.util import email

logger = logging.getLogger(__name__)

# this will assign User to our custom CDCUser
User = get_user_model()


def home(request, template_name="home.html"):
    upcoming_classes = Session.objects.filter(
        is_active=True,
        start_date__gte=timezone.now(),
    ).order_by("start_date")

    if not request.user.is_authenticated or not request.user.role == "mentor":
        upcoming_classes = upcoming_classes.filter(is_public=True)

    upcoming_classes = upcoming_classes[:3]

    return render(request, template_name, {"upcoming_classes": upcoming_classes})


def volunteer(request, template_name="volunteer.html"):
    mentors = (
        Mentor.objects.select_related("user")
        .filter(
            is_active=True,
            is_public=True,
            background_check=True,
            avatar_approved=True,
        )
        .annotate(session_count=Count("mentororder"))
        .order_by("-user__role", "-session_count")
    )

    upcoming_meetings = Meeting.objects.filter(is_active=True, is_public=True, end_date__gte=timezone.now()).order_by(
        "start_date"
    )[:3]

    return render(request, template_name, {"mentors": mentors, "upcoming_meetings": upcoming_meetings})


@login_required
def mentor_approve_avatar(request, pk=None):
    mentor = get_object_or_404(Mentor, id=pk)

    if not request.user.is_staff:
        messages.error(request, "You do not have permissions to moderate content.")

        return redirect(f"{reverse('account_login')}?next={mentor.get_approve_avatar_url()}")

    mentor.avatar_approved = True
    mentor.save()

    if mentor.background_check:
        messages.success(
            request,
            f"{mentor.full_name}'s avatar approved and their account is now public.",
        )

        return redirect(f"{reverse('mentors')}{mentor.id}")

    else:
        messages.success(
            request,
            (f"{mentor.full_name}'s avatar approved but they have yet " f"to fill out the 'background search' form."),
        )

        return redirect("mentors")


@login_required
def mentor_reject_avatar(request, pk=None):
    mentor = get_object_or_404(Mentor, id=pk)

    if not request.user.is_staff:
        messages.error(request, "You do not have permissions to moderate content.")

        return redirect(f"{reverse('account_login')}?next={mentor.get_reject_avatar_url()}")

    mentor.avatar_approved = False
    mentor.save()

    email(
        subject="Your We All Code avatar...",
        template_name="class-announcement-mentor",
        merge_global_data={
            "site_url": settings.SITE_URL,
        },
        recipients=[mentor.email],
    )

    messages.warning(
        request,
        (
            f"{mentor.full_name}'s avatar rejected and their account "
            f"is no longer public. An email notice has been sent to the mentor."
        ),
    )

    return redirect("mentors")


@login_required
def student_detail(request, student_id=False, template_name="student-detail.html"):
    access = True

    if request.user.role == "guardian" and student_id:
        # for the specific student redirect to admin page
        try:
            student = Student.objects.get(id=student_id, is_active=True)
        except ObjectDoesNotExist:
            return redirect("account_home")

        try:
            guardian = Guardian.objects.get(user=request.user, is_active=True)
        except ObjectDoesNotExist:
            return redirect("account_home")

        if not student.guardian == guardian:
            access = False

        form = StudentForm(instance=student)
    else:
        access = False

    if not access:
        return redirect("account_home")
        messages.error(request, "You do not have permissions to edit this student.")

    if request.method == "POST":
        if "delete" in request.POST:
            student.is_active = False
            student.save()
            messages.success(request, f'Student "{student.first_name} {student.last_name}" Deleted.')
            return redirect("account_home")

        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student Updated.")
            return redirect("account_home")

    return render(request, template_name, {"form": form})


@login_required
def cdc_admin(request, template_name="admin.html"):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect("weallcode-home")

    sessions = (
        Session.objects.select_related()
        .annotate(
            num_orders=Count("order"),
            num_attended=Count(Case(When(order__check_in__isnull=False, then=1))),
            is_future=Case(
                When(start_date__gte=timezone.now(), then=1),
                default=0,
                output_field=IntegerField(),
            ),
        )
        .order_by("-start_date")
    )

    meetings = (
        Meeting.objects.select_related()
        .annotate(
            num_orders=Count("meetingorder"),
            num_attended=Count(Case(When(meetingorder__check_in__isnull=False, then=1))),
            is_future=Case(
                When(end_date__gte=timezone.now(), then=1),
                default=0,
                output_field=IntegerField(),
            ),
        )
        .order_by("-start_date")
    )

    orders = Order.objects.select_related()

    total_past_orders = orders.filter(is_active=True)
    total_past_orders_count = total_past_orders.count()
    total_checked_in_orders = orders.filter(is_active=True, check_in__isnull=False)
    total_checked_in_orders_count = total_checked_in_orders.count()

    # Genders
    gender_count = list(Counter(e.student.get_clean_gender() for e in total_checked_in_orders).items())
    gender_count = sorted(list(dict(gender_count).items()), key=operator.itemgetter(1))

    # Ages
    ages = sorted(list(e.student.get_age(e.session.start_date) for e in total_checked_in_orders))
    age_count = sorted(list(dict(list(Counter(ages).items())).items()), key=operator.itemgetter(0))

    # Average Age
    average_age = int(round(sum(ages) / float(len(ages))))

    return render(
        request,
        template_name,
        {
            "age_count": age_count,
            "average_age": average_age,
            "gender_count": gender_count,
            "meetings": meetings,
            # 'past_meetings_count': past_meetings_count,
            # 'past_sessions': past_sessions,
            # 'past_sessions_count': past_sessions_count,
            "sessions": sessions,
            "total_checked_in_orders_count": total_checked_in_orders_count,
            "total_past_orders_count": total_past_orders_count,
            # 'upcoming_meetings': upcoming_meetings,
            # 'upcoming_meetings_count': upcoming_meetings_count,
            # 'upcoming_sessions': upcoming_sessions,
            # 'upcoming_sessions_count': upcoming_sessions_count,
        },
    )


@login_required
@never_cache
def session_stats(request, pk, template_name="session-stats.html"):

    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect("weallcode-home")

    session_obj = get_object_or_404(Session, pk=pk)

    current_orders_checked_in = session_obj.get_current_orders(checked_in=True)

    students_checked_in = current_orders_checked_in.values("student")

    if students_checked_in:
        attendance_percentage = round(
            (float(current_orders_checked_in.count()) / float(session_obj.get_active_student_count())) * 100
        )

    else:
        attendance_percentage = False

    # Genders
    gender_count = list(Counter(e.student.get_clean_gender() for e in session_obj.get_current_orders()).items())

    gender_count = sorted(list(dict(gender_count).items()), key=operator.itemgetter(1))

    # Ages
    ages = sorted(list(e.student.get_age(e.session.start_date) for e in session_obj.get_current_orders()))

    age_count = sorted(list(dict(list(Counter(ages).items())).items()), key=operator.itemgetter(1))

    # Average Age
    average_age = False
    if current_orders_checked_in:
        student_ages = []
        for order in current_orders_checked_in:
            student_ages.append(order.student.get_age(order.session.start_date))

        average_age = reduce(lambda x, y: x + y, student_ages) / len(student_ages)

    return render(
        request,
        template_name,
        {
            "session": session_obj,
            "students_checked_in": students_checked_in,
            "attendance_percentage": attendance_percentage,
            "average_age": average_age,
            "age_count": age_count,
            "gender_count": gender_count,
        },
    )


@login_required
@never_cache
def session_check_in(request, pk, template_name="session_check_in.html"):

    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")

        return redirect("weallcode-home")

    if request.method == "POST":
        if "order_id" in request.POST:
            order = get_object_or_404(Order, id=request.POST["order_id"])

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            if f"{order.guardian.full_name}" != request.POST["order_alternate_guardian"]:
                order.alternate_guardian = request.POST["order_alternate_guardian"]

            order.save()
        else:
            messages.error(request, "Invalid Order")

    # Get current session
    session = get_object_or_404(Session, pk=pk)

    # Active Session
    if timezone.now() < session.end_date:
        active_session = True
    else:
        active_session = False

    # get the orders
    orders = (
        Order.objects.select_related()
        .filter(session_id=pk)
        .annotate(
            num_attended=Count(Case(When(student__order__check_in__isnull=False, then=1))),
            num_missed=Count(Case(When(student__order__check_in__isnull=True, then=1))),
        )
    )

    if active_session:
        active_orders = orders.filter(is_active=True).order_by("student__first_name")

    else:
        active_orders = orders.filter(is_active=True, check_in__isnull=False).order_by("student__first_name")

    inactive_orders = orders.filter(is_active=False).order_by("-updated_at")

    no_show_orders = orders.filter(is_active=True, check_in__isnull=True)

    checked_in_orders = orders.filter(is_active=True, check_in__isnull=False)

    # Genders
    gender_count = sorted(
        list(dict(list(Counter(e.student.get_clean_gender() for e in active_orders).items())).items()),
        key=operator.itemgetter(1),
    )

    # Ages
    ages = sorted(list(e.student.get_age(e.session.start_date) for e in active_orders))

    age_count = sorted(list(dict(list(Counter(ages).items())).items()), key=operator.itemgetter(0))

    # Average Age
    if orders and ages:
        average_age = int(round(sum(ages) / float(len(ages))))
    else:
        average_age = 0

    return render(
        request,
        template_name,
        {
            "session": session,
            "active_session": active_session,
            "active_orders": active_orders,
            "inactive_orders": inactive_orders,
            "no_show_orders": no_show_orders,
            "gender_count": gender_count,
            "age_count": age_count,
            "average_age": average_age,
            "checked_in_orders": checked_in_orders,
        },
    )


@login_required
@never_cache
def session_check_in_mentors(request, pk, template_name="session_check_in_mentors.html"):

    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect("weallcode-home")

    if request.method == "POST":
        if "order_id" in request.POST:
            order = get_object_or_404(MentorOrder, id=request.POST["order_id"])

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            order.save()
        else:
            messages.error(request, "Invalid Order")

    session = get_object_or_404(Session, pk=pk)

    # Active Session
    if timezone.now() < session.end_date:
        active_session = True
    else:
        active_session = False

    # get the orders
    orders = MentorOrder.objects.select_related().filter(session_id=pk)

    if active_session:
        active_orders = orders.filter(is_active=True).order_by("mentor__user__first_name")

    else:
        active_orders = orders.filter(is_active=True, check_in__isnull=False).order_by("mentor__user__first_name")

    inactive_orders = orders.filter(is_active=False).order_by("-updated_at")

    no_show_orders = orders.filter(is_active=True, check_in__isnull=True)

    checked_in_orders = orders.filter(is_active=True, check_in__isnull=False)

    return render(
        request,
        template_name,
        {
            "session": session,
            "active_session": active_session,
            "active_orders": active_orders,
            "inactive_orders": inactive_orders,
            "no_show_orders": no_show_orders,
            "checked_in_orders": checked_in_orders,
        },
    )


@login_required
@never_cache
def session_donations(request, pk, template_name="session_donations.html"):

    # TODO: we should really turn this into a decorator
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect("account_home")

    session = get_object_or_404(Session, pk=pk)

    default_form = DonationForm(initial={"session": session})
    default_form.fields["user"].queryset = User.objects.filter(
        id__in=Order.objects.filter(session=session).values_list("guardian__user__id", flat=True)
    )

    form = default_form

    donations = Donation.objects.filter(session=session)

    if request.method == "POST":
        form = DonationForm(request.POST)
        if form.is_valid():
            form.save()
            form = default_form
            messages.success(request, "Donation added!")

    return render(request, template_name, {"form": form, "session": session, "donations": donations})


@login_required
@never_cache
def meeting_check_in(request, meeting_id, template_name="meeting_check_in.html"):

    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect("account_home")

    if request.method == "POST":
        if "order_id" in request.POST:
            order = get_object_or_404(MeetingOrder, id=request.POST["order_id"])

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            order.save()
        else:
            messages.error(request, "Invalid Order")

    orders = MeetingOrder.objects.select_related().filter(meeting=meeting_id).order_by("mentor__user__first_name")

    active_orders = orders.filter(is_active=True)

    inactive_orders = orders.filter(is_active=False)

    checked_in = orders.filter(is_active=True, check_in__isnull=False)

    return render(
        request,
        template_name,
        {
            "active_orders": active_orders,
            "inactive_orders": inactive_orders,
            "checked_in": checked_in,
        },
    )


@never_cache
def session_announce_mentors(request, pk):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect("home")

    session_obj = get_object_or_404(Session, pk=pk)

    if not session_obj.announced_date_mentors:
        merge_data = {}
        merge_global_data = {
            "class_code": session_obj.course.code,
            "class_title": session_obj.course.title,
            "class_description": session_obj.course.description,
            "class_start_date": arrow.get(session_obj.mentor_start_date).to("local").format("dddd, MMMM D, YYYY"),
            "class_start_time": arrow.get(session_obj.mentor_start_date).to("local").format("h:mma"),
            "class_end_date": arrow.get(session_obj.end_date).to("local").format("dddd, MMMM D, YYYY"),
            "class_end_time": arrow.get(session_obj.end_date).to("local").format("h:mma"),
            "minimum_age": session_obj.minimum_age,
            "maximum_age": session_obj.maximum_age,
            "class_location_name": session_obj.location.name,
            "class_location_address": session_obj.location.address,
            "class_location_city": session_obj.location.city,
            "class_location_state": session_obj.location.state,
            "class_location_zip": session_obj.location.zip,
            "class_additional_info": session_obj.additional_info,
            "class_url": f"{settings.SITE_URL}{session_obj.get_absolute_url()}",
            "class_calendar_url": f"{settings.SITE_URL}{session_obj.get_calendar_url()}",
        }
        recipients = []

        # send mentor announcements
        mentors = Mentor.objects.filter(
            is_active=True,
            user__is_active=True,
        )

        for mentor in mentors:
            recipients.append(mentor.email)
            merge_data[mentor.email] = {
                "first_name": mentor.first_name,
                "last_name": mentor.last_name,
            }

        email(
            subject="New We All Code class date announced! Come mentor!",
            template_name="class-announcement-mentor",
            merge_data=merge_data,
            merge_global_data=merge_global_data,
            recipients=recipients,
            preheader="Help us make a huge difference! A brand new class was just announced.",
            unsub_group_id=settings.SENDGRID_UNSUB_CLASSANNOUNCE,
        )

        session_obj.announced_date_mentors = timezone.now()
        session_obj.save()

        messages.success(request, f"Session announced to {mentors.count()} mentors.")

    else:
        messages.warning(request, f"Session already announced.")

    return redirect("cdc-admin")


@never_cache
def session_announce_guardians(request, pk):
    if not request.user.is_staff:
        messages.error(request, "You do not have permission to access this page.")
        return redirect("home")

    session_obj = get_object_or_404(Session, pk=pk)

    if not session_obj.announced_date_guardians:
        merge_data = {}
        merge_global_data = {
            "class_code": session_obj.course.code,
            "class_title": session_obj.course.title,
            "class_description": session_obj.course.description,
            "class_start_date": arrow.get(session_obj.start_date).to("local").format("dddd, MMMM D, YYYY"),
            "class_start_time": arrow.get(session_obj.start_date).to("local").format("h:mma"),
            "class_end_date": arrow.get(session_obj.end_date).to("local").format("dddd, MMMM D, YYYY"),
            "class_end_time": arrow.get(session_obj.end_date).to("local").format("h:mma"),
            "minimum_age": session_obj.minimum_age,
            "maximum_age": session_obj.maximum_age,
            "class_location_name": session_obj.location.name,
            "class_location_address": session_obj.location.address,
            "class_location_city": session_obj.location.city,
            "class_location_state": session_obj.location.state,
            "class_location_zip": session_obj.location.zip,
            "class_additional_info": session_obj.additional_info,
            "class_url": f"{settings.SITE_URL}{session_obj.get_absolute_url()}",
            "class_calendar_url": f"{settings.SITE_URL}{session_obj.get_calendar_url()}",
        }
        recipients = []

        guardians = Guardian.objects.filter(
            is_active=True,
            user__is_active=True,
        )

        for guardian in guardians:
            recipients.append(guardian.email)
            merge_data[guardian.email] = {
                "first_name": guardian.first_name,
                "last_name": guardian.last_name,
            }

        email(
            subject="New We All Code class date announced!",
            template_name="class-announcement-guardian",
            merge_data=merge_data,
            merge_global_data=merge_global_data,
            recipients=recipients,
            preheader="We're super excited to bring you another class date. Sign up to reserve your spot",
            unsub_group_id=settings.SENDGRID_UNSUB_CLASSANNOUNCE,
        )

        session_obj.announced_date_guardians = timezone.now()
        session_obj.save()

        messages.success(request, f"Session announced to {guardians.count()} guardians!")

    else:
        messages.warning(request, "Session already announced.")

    return redirect("cdc-admin")


@csrf_exempt
# the "service" that computers run to self update
def check_system(request):
    # set up variables
    runUpdate = True
    responseString = ""
    cmdString = (
        'sh -c "$(curl -fsSL ' "https://raw.githubusercontent.com/CoderDojoChi" '/linux-update/master/update.sh)"'
    )
    halfday = timedelta(hours=12)
    # halfday = timedelta(seconds=15)

    if Session.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
    ).count():
        runUpdate = False

    # uuid is posted from the computer using a bash script
    # see:
    # https://raw.githubusercontent.com/CoderDojoChi
    # /linux-update/master/etc/init.d/coderdojochi-phonehome
    uuid = request.POST.get("uuid")

    if uuid:
        equipmentType = EquipmentType.objects.get(name="Laptop")
        if equipmentType:
            equipment, created = Equipment.objects.get_or_create(uuid=uuid, defaults={"equipment_type": equipmentType})

            # check for blank values of last_system_update.
            # If blank, assume we need to run it
            if not equipment.last_system_update:
                equipment.force_update_on_next_boot = True

            # do we need to update?
            if runUpdate and (
                equipment.force_update_on_next_boot or (timezone.now() - equipment.last_system_update > halfday)
            ):
                responseString = cmdString
                equipment.last_system_update = timezone.now()
                equipment.force_update_on_next_boot = False

            # update the last_system_update_check_in to now
            equipment.last_system_update_check_in = timezone.now()
            equipment.save()

    return HttpResponse(responseString)
