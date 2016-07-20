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

    if orders.count():
        button_modifier = 'btn-cdc-danger'
        button_msg = 'Can\'t make it'
    else:
        button_modifier = ''
        button_msg = 'Enroll'

    form = '<a href="{}" class="btn-cdc btn-cdc-sm {}">{}</a>'.format(
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
        ),
        button_modifier,
        button_msg
        )

    return Template(form).render(context)

