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
            message = (
                f"Sorry, this class is limited to {session.gender_limitation}s between {session.minimum_age} "
                f"and {session.maximum_age} this time around."
            )

            button_href = (
                'data-trigger="hover" data-placement="top" data-toggle="popover" title="" '
                f'data-content="{message}" data-original-title="{title}"'
            )

        elif not student.is_within_age_range(session.minimum_age, session.maximum_age, session.start_date):
            title = "Age-limited event."
            message = (
                f"Sorry, this class is limited to student between ages {session.minimum_age} and "
                f"{session.maximum_age} this time around."
            )
            button_href = (
                'data-trigger="hover" data-placement="top" data-toggle="popover" title="" '
                f'data-content="{message}" data-original-title="{title}"'
            )

        elif not student.is_within_gender_limitation(session.gender_limitation):
            if session.gender_limitation == "female":
                title = "Girls-only event."
            else:
                title = "Boys-only event."

            message = f"Sorry, this class is limited to {session.gender_limitation}s this time around."
            button_href = (
                'data-trigger="hover" data-placement="top" data-toggle="popover" title="" '
                f'data-content="{message}" data-original-title="{title}" '
            )

    form = (
        f"<{button_tag} {button_href} class='button small {button_modifier}' {button_additional_attributes}>"
        f"{button_msg}"
        f"</{button_tag}>"
    )

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
