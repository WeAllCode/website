# -*- coding: utf-8 -*-
import arrow

from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        # evil ValueError that doesn't tell you what the wrong value was
        raise ValueError


def local_to_utc(date):
    return arrow.get(date).replace(tzinfo='America/Chicago').to('UTC')


def email(subject, template_name, context, recipients, preheader, send=True):
    if not (subject and template_name and context and recipients):
        return False

    if not isinstance(recipients, list):
        return False

    context['subject'] = subject
    context['current_year'] = timezone.now().year
    context['company_name'] = settings.SITE_NAME
    context['site_url'] = settings.SITE_URL

    if preheader:
        context['preheader'] = preheader

    html_content = render_to_string('{}.html'.format(template_name), context)
    text_content = render_to_string('{}.txt'.format(template_name), context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients
    )
    msg.attach_alternative(html_content, "text/html")

    if send:
        msg.send()

    return msg
