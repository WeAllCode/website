import logging
import re
import time
from email.utils import formataddr

import sentry_sdk
from anymail.message import AnymailMessage
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from coderdojochi.models import EmailSuppression

logger = logging.getLogger(__name__)

User = get_user_model()

MERGE_FIELD_FORMAT = "*|{}|*"
LEFTOVER_MERGE_FIELD = re.compile(r"\*\|\w+\|\*")
UNSUBSCRIBE_SALT = "email-unsubscribe"
SEND_INTERVAL_SECONDS = 0.6

# Optional mail: an unsubscribe link or a SendGrid group unsubscribe opts people out.
ANNOUNCEMENT_TEMPLATES = frozenset(
    {
        "class_announcement_guardian",
        "class_announcement_mentor",
        "meeting_announcement_mentor",
        "birthday_mentor",
        "first_class_guardian",
    },
)
# These reasons block announcements only; every other reason blocks all mail.
ANNOUNCEMENT_ONLY_REASONS = frozenset(
    {
        EmailSuppression.GROUP_UNSUBSCRIBE,
        EmailSuppression.USER_UNSUBSCRIBE,
    },
)


def unsubscribe_token(email_address):
    return signing.dumps(email_address.strip().lower(), salt=UNSUBSCRIBE_SALT)


def unsubscribe_email_from_token(token):
    """Return the token's email; raise `signing.BadSignature` if it was forged."""
    return signing.loads(token, salt=UNSUBSCRIBE_SALT)


def unsubscribe_url(email_address):
    path = reverse(
        "email-unsubscribe",
        kwargs={"token": unsubscribe_token(email_address)},
    )
    return f"{settings.SITE_URL}{path}"


def fill_merge_fields(text, values):
    """Replace each `*|key|*` with its value (None is ""), then drop leftover tags."""
    for key, val in values.items():
        text = text.replace(
            MERGE_FIELD_FORMAT.format(key),
            "" if val is None else str(val),
        )
    return LEFTOVER_MERGE_FIELD.sub("", text)


def email_daily_limit():
    return getattr(settings, "EMAIL_DAILY_LIMIT", 90)


def deliverable_recipients(recipients, template_name=None):
    """Return `recipients` minus suppressed addresses (case-insensitive).

    Group and link unsubscribes only block the announcement templates.
    """
    suppressions = EmailSuppression.objects.filter(
        email__in={recipient.strip().lower() for recipient in recipients},
    )
    if template_name not in ANNOUNCEMENT_TEMPLATES:
        suppressions = suppressions.exclude(reason__in=ANNOUNCEMENT_ONLY_REASONS)
    suppressed = set(suppressions.values_list("email", flat=True))
    return [r for r in recipients if r.strip().lower() not in suppressed]


def _drop_suppressed(recipients, template_name):
    kept = deliverable_recipients(recipients, template_name)
    if len(kept) < len(recipients):
        logger.info(
            "Skipping %d suppressed recipient(s) for '%s'.",
            len(recipients) - len(kept),
            template_name,
        )
    return kept


def _check_daily_limit(recipients, template_name):
    daily_limit = email_daily_limit()
    if len(recipients) > daily_limit:
        message = (
            f"Refusing to send '{template_name}' to {len(recipients)} recipients;"
            f" the limit is {daily_limit} per day. Nothing was sent."
        )
        logger.error(message)
        raise ValueError(message)


def _deactivate_rejected(msg):
    for recipient, send_attempt in msg.anymail_status.recipients.items():
        if send_attempt.status in ["queued", "sent"]:
            continue
        logger.error("user: %s, %s", recipient, timezone.now())
        user = User.objects.filter(email__iexact=recipient).first()
        if user is None:
            continue
        user.is_active = False
        user.admin_notes = (
            f"User '{send_attempt.reject_reason}' when checked on {timezone.now()}"
        )
        user.save()


def _sendgrid_extra(template_name, unsub_group_id):
    esp_extra = {"categories": [template_name]}
    if unsub_group_id:
        esp_extra["asm"] = {"group_id": unsub_group_id}
    return esp_extra


def _send(msg, recipient, template_name):
    """Send one message. On failure, report to Sentry and return False."""
    try:
        msg.send()
    except Exception as e:  # noqa: BLE001 - one bad address must not stop the rest.
        logger.error("Failed to send '%s' to %s: %s", template_name, recipient, e)  # noqa: TRY400
        with sentry_sdk.new_scope() as scope:
            scope.set_tag("email_template", template_name)
            scope.set_extra("recipient", recipient)
            sentry_sdk.capture_exception(e)
        return False
    _deactivate_rejected(msg)
    return True


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
    unsub_group_id=None,
):
    # batch_size is kept for callers; every recipient now gets their own message.
    merge_global_data = dict(merge_global_data)

    if not (subject and template_name and recipients):
        raise ValueError(
            "Missing required parameters: 'subject', 'template_name', and 'recipients' are all required."
        )

    if not isinstance(recipients, list):
        raise TypeError("recipients must be a list")

    # bcc is set to False by default.
    # make sure bcc is in a list form when sent over
    if bcc not in [False, None] and not isinstance(bcc, list):
        raise TypeError("recipients must be a list")

    using_sendgrid = "sendgrid" in settings.EMAIL_BACKEND

    merge_global_data["subject"] = subject
    merge_global_data["current_year"] = timezone.now().year
    merge_global_data["company_name"] = settings.SITE_NAME
    merge_global_data["site_url"] = settings.SITE_URL
    merge_global_data["preheader"] = preheader
    # The base template shows SendGrid's own unsubscribe links when this is set.
    merge_global_data["unsub_group_id"] = unsub_group_id if using_sendgrid else None

    recipients = _drop_suppressed(recipients, template_name)
    if not recipients:
        return
    _check_daily_limit(recipients, template_name)

    # Django renders first; the *|key|* placeholders are filled per recipient after.
    body = render_to_string(f"{template_name}.html", merge_global_data)

    esp_extra = (
        _sendgrid_extra(template_name, unsub_group_id) if using_sendgrid else None
    )

    unsent = []
    for index, recipient in enumerate(recipients):
        if index:
            time.sleep(SEND_INTERVAL_SECONDS)

        values = {**merge_global_data, **merge_data.get(recipient, {})}
        values["unsubscribe_url"] = unsubscribe_url(recipient)

        msg = AnymailMessage(
            subject=fill_merge_fields(subject, values),
            body=fill_merge_fields(body, values),
            from_email=formataddr(("We All Code", settings.DEFAULT_FROM_EMAIL)),
            to=[recipient],
            reply_to=reply_to,
        )
        if esp_extra:
            msg.esp_extra = esp_extra

        msg.content_subtype = "html"

        if mixed_subtype:
            msg.mixed_subtype = mixed_subtype

        for attachment in attachments:
            msg.attach(attachment)

        if not _send(msg, recipient, template_name):
            unsent.append(recipient)

    if unsent:
        logger.error(
            "'%s' was not sent to %d recipient(s): %s",
            template_name,
            len(unsent),
            ", ".join(unsent),
        )


def batches(items, batch_size):
    """
    Split a list into smaller batches of a specified size.

    Args:
        items (list): The list of items to be split into batches
        batch_size (int): The maximum number of items per batch

    Yields:
        list: A batch containing up to batch_size items from the original list

    Example:
        >>> list(batches([1, 2, 3, 4, 5], 2))
        [[1, 2], [3, 4], [5]]
    """
    for start_index in range(0, len(items), batch_size):
        yield items[start_index : start_index + batch_size]
