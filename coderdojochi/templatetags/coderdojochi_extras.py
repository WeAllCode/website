import re

from django import template
from django.urls import reverse
from django.utils.html import format_html

from coderdojochi.models import Order

register = template.Library()


@register.filter
def subtract(value, arg):
    return value - arg


@register.simple_tag(takes_context=False)
def student_session_order_count(student, session):
    orders_count = Order.objects.filter(
        student=student,
        session=session,
        is_active=True,
    ).count()

    return orders_count


@register.simple_tag
def student_register_link(student, session):
    """Render the Enroll / Can't make it control for one student.

    Every value is escaped by `format_html`, and the markup is returned as is:
    session fields are data, never template source.
    """

    url = reverse(
        "session-sign-up",
        kwargs={
            "pk": session.id,
            "student_id": student.id,
        },
    )

    if Order.objects.filter(
        student=student,
        session=session,
        is_active=True,
    ).exists():
        return format_html(
            '<a href="{}" class="cta cta-small cta-tertiary">Can\'t make it</a>',
            url,
        )

    in_age_range = student.is_within_age_range(
        session.minimum_age,
        session.maximum_age,
        session.start_date,
    )
    in_gender_limitation = student.is_within_gender_limitation(
        session.gender_limitation,
    )

    if in_age_range and in_gender_limitation:
        return format_html('<a href="{}" class="cta cta-small">Enroll</a>', url)

    if not in_age_range and not in_gender_limitation:
        title = "Limited event."
        message = (
            f"Sorry, this class is limited to {session.gender_limitation}s"
            f" between {session.minimum_age} and"
            f" {session.maximum_age} this time around."
        )
    elif not in_age_range:
        title = "Age-limited event."
        message = (
            "Sorry, this class is limited to student between ages"
            f" {session.minimum_age} and {session.maximum_age} this time"
            " around."
        )
    else:
        title = (
            "Girls-only event."
            if session.gender_limitation == "female"
            else "Boys-only event."
        )
        message = (
            f"Sorry, this class is limited to {session.gender_limitation}s"
            " this time around."
        )

    # One eligibility hint for all three reasons. A natively disabled button
    # can't take focus or interest, so the trigger is an `aria-disabled`
    # button that does nothing when pressed.
    hint_id = f"eligibility-hint-{session.id}-{student.id}"

    return format_html(
        '<button type="button" class="cta cta-small" aria-disabled="true"'
        ' interestfor="{hint_id}" aria-describedby="{hint_id}">Enroll</button>'
        '<div popover="hint" role="tooltip" id="{hint_id}" class="hint">'
        "<strong>{title}</strong> {message}</div>",
        hint_id=hint_id,
        title=title,
        message=message,
    )


@register.filter
def student_age(student, date):
    return student.get_age(date)


@register.filter(name="phone_number")
def phone_number(str):
    """Convert a 10 character string into 'xxx-xxx-xxxx'."""

    # Strip out all non-digits
    number = re.sub("[^0-9]", "", str)

    # If the number is greater than 11 characters, return it as-is
    if len(number) > 11:
        return str

    # Default country code to nothing
    country_code = ""

    # If the number is 10 characters long, assume it's a US number
    if len(number) == 11:
        # If the first character is 1, strip it out
        if number[0] != "1":
            country_code = f"+{number[0]} "

        # Remove the country code from the number
        number = number[1:]

    # First three digits are the area code
    first = number[0:3]

    # Second three digits are the exchange
    second = number[3:6]

    # Last four digits are the subscriber number
    third = number[6:10]

    # Return the formatted number
    return f"{country_code}{first}-{second}-{third}"
