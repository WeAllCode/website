import logging

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger("mechanize")


def str_to_bool(s):
    TRUE = ['true', 't', '1', 'yes', 'y']
    FALSE = ['false', 'f', '0', 'no', 'n']

    if s.lower() in TRUE:
        return True
    elif s.lower() in FALSE:
        return False
    else:
        # evil ValueError that doesn't
        # tell you what the wrong value was
        raise ValueError


def email(
    subject,
    template_name,
    context,
    recipients,
    preheader=None,
    bcc=None,
    reply_to=None,
    send=True
):

    from django.conf import settings

    if not (subject and template_name and context and recipients):
        raise NameError()

    if not isinstance(recipients, list):
        raise TypeError("recipients must be a list")

    # bcc is set to False by default.
    # make sure bcc is in a list form when sent over
    if bcc not in [False, None] and not isinstance(bcc, list):
        raise TypeError("recipients must be a list")

    context['subject'] = subject
    context['current_year'] = timezone.now().year
    context['company_name'] = settings.SITE_NAME
    context['site_url'] = settings.SITE_URL

    if preheader:
        context['preheader'] = preheader

    html_content = render_to_string(f"{template_name}.html", context)
    text_content = render_to_string(f"{template_name}.txt", context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=f"CoderDojoChi<{settings.DEFAULT_FROM_EMAIL}>",
        to=recipients
    )

    if reply_to:
        msg.reply_to = reply_to

    msg.inline_css = True
    msg.attach_alternative(html_content, "text/html")

    if send:
        try:
            msg.send()
        except Exception as e:
            logger.error(e)
            logger.error(msg)
            response = msg.mandrill_response[0]
            logger.error(response)

            reject_reasons = [
                'hard-bounce',
                'soft-bounce',
                'spam',
                'unsub',
                'custom',
            ]

            if (
                response['status'] == 'rejected' and
                response['reject_reason'] in reject_reasons
            ):
                logger.error(
                    f"user: {response['email']}, {timezone.now()}"
                )

                from coderdojochi.models import CDCUser
                user = CDCUser.objects.get(email=response['email'])
                user.is_active = False
                user.admin_notes = f"User '{response['reject_reason']}' when checked on {timezone.now()}"
                user.save()
            else:
                raise e

    return msg
