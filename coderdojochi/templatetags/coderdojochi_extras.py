import re

from django import template
from django.template import Template
from django.urls import reverse

from coderdojochi.models import Order

register = template.Library()


@register.filter
def subtract(value, arg):
    return value - arg


@register.simple_tag(takes_context=False)
def student_session_order_count(student, session):
    orders_count = Order.objects.filter(student=student, session=session).count()

    return orders_count


@register.simple_tag(takes_context=True)
def student_register_link(context, student, session):
    orders = Order.objects.filter(student=student, session=session, is_active=True)

    url = reverse(
        "session-sign-up",
        kwargs={
            "pk": session.id,
            "student_id": student.id,
        },
    )

    button_tag = "a"
    button_modifier = ""
    button_additional_attributes = ""
    button_msg = "Enroll"
    button_href = f"href={url}"
    prerequisite_needed_buttons = ""

    if orders.count():
        button_modifier = "tertiary"
        button_msg = "Can't make it"

    elif not student.is_within_age_range(
        session.minimum_age, session.maximum_age, session.start_date
    ) or not student.is_within_gender_limitation(session.gender_limitation):
        button_modifier = "btn-default"
        button_additional_attributes = "disabled"
        button_tag = "span"

        if not student.is_within_age_range(
            session.minimum_age, session.maximum_age, session.start_date
        ) and not student.is_within_gender_limitation(session.gender_limitation):
            title = "Limited event."
            message = f"Sorry, this class is limited to {session.gender_limitation}s between {session.minimum_age} and {session.maximum_age} this time around."

            button_href = f'data-trigger="hover" data-placement="top" data-toggle="popover" title="" data-content="{message}" data-original-title="{title}"'

        elif not student.is_within_age_range(session.minimum_age, session.maximum_age, session.start_date):
            title = "Age-limited event."
            message = f"Sorry, this class is limited to student between ages {session.minimum_age} and {session.maximum_age} this time around."

            button_href = f'data-trigger="hover" data-placement="top" data-toggle="popover" title="" data-content="{message}" data-original-title="{title}"'

        elif not student.is_within_gender_limitation(session.gender_limitation):
            if session.gender_limitation == "female":
                title = "Girls-only event."
            else:
                title = "Boys-only event."

            message = f"Sorry, this class is limited to {session.gender_limitation}s this time around."
            button_href = f'data-trigger="hover" data-placement="top" data-toggle="popover" title="" data-content="{message}" data-original-title="{title}" '

    else:
        # Get the prerequisites the student still needs to take in order to attend the current session.
        course_prerequisites_needed = list(session.get_course_prerequisites_needed(student).values("id", "code"))

        if len(course_prerequisites_needed) > 0:
            # When there are outstanding prerequisites, add buttons to navigate to future sessions (if available; disabled otherwise).
            for course_prerequisite in course_prerequisites_needed:
                needed_course_id = course_prerequisite["id"]
                upcoming_prerequisite_sessions = context["upcoming_prerequisite_sessions"]

                if needed_course_id in upcoming_prerequisite_sessions:
                    session_id = upcoming_prerequisite_sessions[needed_course_id]["id"]
                    url = reverse("session-detail", kwargs={"pk": session_id})
                    button_tag = "a"
                    button_href = f"href='{url}'"
                    title = "There is an upcoming session for this prerequisite."
                    button_additional_attributes = f"data-tooltip aria-haspopup='true' title='{title}'"
                else:
                    button_tag = "span"
                    button_href = ""
                    title = "No upcoming session for this prerequisite."
                    button_additional_attributes = f"data-tooltip aria-haspopup='true' title='{title}' disabled"

                button_modifier = "has-tip"
                button_msg = course_prerequisite["code"]
                prerequisite_needed_buttons += f"<{button_tag} {button_href} class='button {button_modifier}' {button_additional_attributes}>{button_msg}</{button_tag}>"

            button_tag = "span"
            button_modifier = "has-tip"
            button_additional_attributes = "disabled"
            button_msg = "Enroll"
            title = f"Sorry, this class has prerequisites that have not been met by {student.first_name} yet."
            button_href = f'data-tooltip aria-haspopup="true" title="{title}"'

    form = f"<{button_tag} {button_href} class='button small {button_modifier}' {button_additional_attributes}>{button_msg}</{button_tag}>"

    if prerequisite_needed_buttons:
        form += f"<br /><div class='tiny button-group align-right'>{prerequisite_needed_buttons}</div>"

    return Template(form).render(context)


@register.filter
def student_age(student, date):
    return student.get_age(date)


@register.simple_tag(takes_context=True)
def menu_is_active(context, pattern_or_urlname, css_class="active"):
    try:
        pattern = "^" + reverse(pattern_or_urlname)
    except NoReverseMatch:
        pattern = pattern_or_urlname

    if re.search(pattern, context["request"].path):
        return css_class
    else:
        return ""
