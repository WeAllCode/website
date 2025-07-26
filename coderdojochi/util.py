import logging
from itertools import batched
from typing import Any

from anymail.message import AnymailMessage
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()


def email(
    subject: str,
    template_name: str,
    attachments: list[Any] | None = None,
    batch_size: int = 500,
    bcc: list[str] | None | bool = None,
    merge_data: dict[str, Any] | None = None,
    merge_global_data: dict[str, Any] | None = None,
    mixed_subtype: str | None = None,
    preheader: str | None = None,
    recipients: list[str] | None = None,
    reply_to: str | None = None,
    unsub_group_id: int | None = None,
) -> None:
    # Handle mutable default arguments
    if attachments is None:
        attachments = []
    if merge_data is None:
        merge_data = {}
    if merge_global_data is None:
        merge_global_data = {}
    if recipients is None:
        recipients = []

    if not (subject and template_name and recipients):
        raise ValueError("Missing required parameters: 'subject', 'template_name', and 'recipients' are all required.")

    if not isinstance(recipients, list):
        raise TypeError("recipients must be a list")

    # bcc is set to False by default.
    # make sure bcc is in a list form when sent over
    if bcc not in [False, None] and not isinstance(bcc, list):
        raise TypeError("recipients must be a list")

    merge_global_data["subject"] = subject
    merge_global_data["current_year"] = timezone.now().year
    merge_global_data["company_name"] = settings.SITE_NAME
    merge_global_data["site_url"] = settings.SITE_URL
    merge_global_data["preheader"] = preheader
    merge_global_data["unsub_group_id"] = unsub_group_id

    body = render_to_string(f"{template_name}.html", merge_global_data)

    # If we send values that don't exist in the template,
    # SendGrid divides by zero, doesn't pass go, does not collect $200.
    merge_field_format = "*|{}|*"
    final_merge_global_data = {}
    for key, val in merge_global_data.items():
        if merge_field_format.format(key) in body:
            if val is None:
                final_merge_global_data[key] = ""
            else:
                final_merge_global_data[key] = str(val)

    esp_extra = {
        "merge_field_format": merge_field_format,
        "categories": [template_name],
    }

    if unsub_group_id:
        esp_extra["asm"] = {
            "group_id": unsub_group_id,
        }

    for recipients_batch in batched(recipients, batch_size):
        msg = AnymailMessage(
            subject=subject,
            body=body,
            from_email=f"We All Code<{settings.DEFAULT_FROM_EMAIL}>",
            to=recipients_batch,
            reply_to=reply_to,
            merge_data=merge_data,
            merge_global_data=final_merge_global_data,
            esp_extra=esp_extra,
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
            if send_attempt.status not in ["queued", "sent"]:
                logger.error(f"user: {recipient}, {timezone.now()}")

                user = User.objects.get(email=recipient)
                user.is_active = False
                user.admin_notes = (
                    f"User '{send_attempt.reject_reason}' when checked on"
                    f" {timezone.now()}"
                )
                user.save()



