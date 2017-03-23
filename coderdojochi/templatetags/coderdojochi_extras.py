from django import template
from django.template import Template
from django.core.urlresolvers import reverse

from coderdojochi.models import Order

register = template.Library()


@register.filter
def subtract(value, arg):
    return value - arg


@register.assignment_tag(takes_context=False)
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
                '{:02}'.format(session.start_date.month),
                '{:02}'.format(session.start_date.day),
                session.course.slug,
                session.id,
                student.id
            )
        )
    )

    if orders.count():
        button_modifier = 'btn-cdc-danger'
        button_msg = 'Can\'t make it'

    elif (
        not student.is_within_age_range(
            session.min_age_limitation,
            session.max_age_limitation
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
                session.max_age_limitation
            ) and
            not student.is_within_gender_limitation(
                session.gender_limitation
            )
        ):
            button_href = '''
                data-trigger="hover" data-placement="top" data-toggle="popover"
                title="" data-content="Sorry, this class is limited to {}s
                between {} and {} this time around."
                data-original-title="Limited event."
            '''.format(
                session.gender_limitation,
                session.min_age_limitation,
                session.max_age_limitation
            )

        elif (
            not student.is_within_age_range(
                session.min_age_limitation,
                session.max_age_limitation
            )
        ):
            button_href = '''
                data-trigger="hover" data-placement="top" data-toggle="popover"
                title="" data-content="Sorry, this class is limited to
                student between ages {} and {} this time around."
                data-original-title="Age-limited event."
            '''.format(
                session.min_age_limitation,
                session.max_age_limitation
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

    form = '<{0} {1} class="btn-cdc btn-cdc-sm {2}" {3}>{4}</{0}>'.format(
        button_tag,
        button_href,
        button_modifier,
        button_additional_attributes,
        button_msg
    )

    return Template(form).render(context)
