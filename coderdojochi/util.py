import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from anymail.exceptions import AnymailAPIError
from anymail.message import AnymailMessage

logger = logging.getLogger(__name__)


def email(
    subject,
    template_name,
    attachments=[],
    batch_size=500,
    bcc=None,
    merge_data={},
    merge_global_data={},
    mixed_subtype=None,
    preheader=None,
    recipients=[],
    reply_to=None,
):

    if not (subject and template_name and recipients):
        raise NameError()

    if not isinstance(recipients, list):
        raise TypeError("recipients must be a list")

    # bcc is set to False by default.
    # make sure bcc is in a list form when sent over
    if bcc not in [False, None] and not isinstance(bcc, list):
        raise TypeError("recipients must be a list")

    merge_global_data['subject'] = subject
    merge_global_data['current_year'] = timezone.now().year
    merge_global_data['company_name'] = settings.SITE_NAME
    merge_global_data['site_url'] = settings.SITE_URL
    merge_global_data['preheader'] = preheader

    body = render_to_string(f"{template_name}.html", merge_global_data)

    # If we send values that don't exist in the template,
    # SendGrid divides by zero, doesn't pass go, does not collect $200.
    merge_field_format = "*|{}|*"
    final_merge_global_data = {}
    for key, val in merge_global_data.items():
        if merge_field_format.format(key) in body:
            final_merge_global_data[key] = "" if val is None else str(val)

    for recipients_batch in batches(recipients, batch_size):
        msg = AnymailMessage(
            subject=subject,
            body=body,
            from_email=f"We All Code<{settings.DEFAULT_FROM_EMAIL}>",
            to=recipients_batch,
            reply_to=reply_to,
            merge_data=merge_data,
            merge_global_data=final_merge_global_data,
            esp_extra={
                'merge_field_format': merge_field_format,
                'categories': [template_name],
                'asm': {
                    'group_id': settings.DEFAULT_UNSUB_GROUP
                }
            },
        )

        msg.content_subtype = "html"

        if mixed_subtype:
            msg.mixed_subtype = mixed_subtype

        for attachment in attachments:
            msg.attach(attachment)

        try:
            msg.send()
        except Exception as e:
            logger.error(e)
            logger.error(msg)
            raise e

        for recipient in msg.anymail_status.recipients.keys():
            send_attempt = msg.anymail_status.recipients[recipient]
            if send_attempt.status not in ['queued', 'sent']:
                logger.error(
                    f"user: {recipient}, {timezone.now()}"
                )

                from coderdojochi.models import CDCUser
                user = CDCUser.objects.get(email=recipient)
                user.is_active = False
                user.admin_notes = f"User '{send_attempt.reject_reason}' when checked on {timezone.now()}"
                user.save()



def batches(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]
