from django import template
from django.core.urlresolvers import reverse

from coderdojochi.models import Order

register = template.Library()

@register.filter
def subtract(value, arg):
    return value - arg


@register.simple_tag
def student_register_link(student, session):

    orders = Order.objects.filter(student=student, session=session)

    if orders.count():
        button_type = 'danger'
        button_msg = 'Can\'t make it'
    else:
        button_type = 'success'
        button_msg = 'Enroll'

    link = form = '<a href="' + reverse('session_sign_up', args=(session.start_date.year, session.start_date.month, session.start_date.day, session.course.slug, student.id)) + '" class="btn btn-' + button_type + '">' + button_msg + '</a>'

    return form

