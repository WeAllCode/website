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
    orders_count = Order.objects.filter(student=student, session=session).count()
    return orders_count

@register.simple_tag(takes_context=True)
def student_register_link(context, student, session):
    orders = Order.objects.filter(student=student, session=session, active=True)

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
    elif session.gender_limitation and student.get_clean_gender() not in  [
        session.gender_limitation,
        'other'
    ]:
        button_modifier = 'btn-default'
        button_additional_attributes = 'disabled'
        button_tag = 'span'
        button_href = ''' data-trigger="hover" data-placement="top" data-toggle="popover"
                      title="" data-content="Sorry, this class is limited to {}s this time
                      around." data-original-title="No {} allowed!"
                      '''.format(
                          session.gender_limitation,
                          'boys' if session.gender_limitation == 'female' else 'girls'
                      )

    form = '<{0} {1} class="btn-cdc btn-cdc-sm {2}" {3}>{4}</{0}>'.format(
        button_tag,
        button_href,
        button_modifier,
        button_additional_attributes,
        button_msg
    )

    return Template(form).render(context)

