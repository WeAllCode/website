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
    orders_count = Order.objects.filter(
        student=student,
        session=session
    ).count()

    return orders_count


@register.simple_tag(takes_context=True)
def student_register_link(context, student, session):
    orders = Order.objects.filter(
        student=student,
        session=session,
        is_active=True
    )

    button_tag = 'a'
    button_modifier = ''
    button_additional_attributes = ''
    button_msg = 'Enroll'
    button_href = 'href={}'.format(
        reverse(
            'session_sign_up',
            args=(
                session.start_date.year,
                f"{session.start_date.month:02}",
                f"{session.start_date.day:02}",
                session.course.slug,
                session.id,
                student.id
            )
        )
    )

    if orders.count():
        button_modifier = "btn-cdc-danger"
        button_msg = "Can't make it"

    elif (
        not student.is_within_age_range(
            session.min_age_limitation,
            session.max_age_limitation,
            session.start_date
        ) or
        not student.is_within_gender_limitation(
            session.gender_limitation
        )
    ):
        button_modifier = 'btn-default'
        button_additional_attributes = 'disabled'
        button_tag = 'span'

        if (
            not student.is_within_age_range(
                session.min_age_limitation,
                session.max_age_limitation,
                session.start_date
            ) and
            not student.is_within_gender_limitation(
                session.gender_limitation
            )
        ):
            button_href = (
                f"data-trigger='hover' data-placement='top' data-toggle='popover' title=' "
                f"data-content='Sorry, this class is limited to {session.gender_limitation}s "
                f"between {session.min_age_limitation} and {session.max_age_limitation} this time around.' "
                f"data-original-title='Limited event.'"
            )

        elif (
            not student.is_within_age_range(
                session.min_age_limitation,
                session.max_age_limitation,
                session.start_date
            )
        ):
            button_href = (
                f"data-trigger='hover' data-placement='top' data-toggle='popover' "
                f"title=' data-content='Sorry, this class is limited to student between "
                f"ages {session.min_age_limitation} and {session.max_age_limitation} this time around.' "
                f"data-original-title='Age-limited event.' "
            )

        elif (
            not student.is_within_gender_limitation(
                session.gender_limitation
            )
        ):
            button_href = '''
                data-trigger="hover" data-placement="top" data-toggle="popover"
                title="" data-content="Sorry, this class is limited to {}s
                this time around." data-original-title="{}-only event."
            '''.format(
                session.gender_limitation,
                'Girls' if session.gender_limitation == 'female' else 'Boys'
            )

    form = (
        f"<{button_tag} {button_href} class='btn-cdc btn-cdc-sm {button_modifier}' {button_additional_attributes}>"
        f"{button_msg}"
        f"</{button_tag}>"
    )

    return Template(form).render(context)


@register.filter
def student_age(student, date):
    return student.get_age(date)
