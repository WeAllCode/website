from django import template
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

@register.simple_tag
def student_register_link(student, session):

    orders = Order.objects.filter(student=student, session=session)

    if orders.count():
        button_modifier = ' btn-cdc-danger'
        button_msg = 'Can\'t make it'
    else:
        button_modifier = ''
        button_msg = 'Enroll'

    link = form = '<a href="' + reverse('session_sign_up', args=(session.start_date.year, format(session.start_date.month, '02'), format(session.start_date.day, '02'), session.course.slug, session.id, student.id)) + '" class="btn-cdc btn-cdc-sm'+ button_modifier + '">' + button_msg + '</a>'

    return form

