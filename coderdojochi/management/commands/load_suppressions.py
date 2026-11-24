import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from coderdojochi.models import EmailSuppression

# When an address is in several lists, the first reason here wins.
LIST_REASONS = [
    ("spam_reports", EmailSuppression.SPAM_REPORT),
    ("bounces", EmailSuppression.BOUNCE),
    ("blocks", EmailSuppression.BLOCK),
    ("unsubscribes", EmailSuppression.UNSUBSCRIBE),
]


def _email_of(item):
    if isinstance(item, dict):
        item = item.get("email")
    if not isinstance(item, str):
        return ""
    return item.strip().lower()


class Command(BaseCommand):
    help = "Load exported SendGrid suppression lists. Safe to run more than once."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            help="SendGrid suppressions export (JSON)",
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            message = f"Could not read {path}: {e}"
            raise CommandError(message) from e

        reasons = {}
        for key, reason in LIST_REASONS:
            for item in data.get(key) or []:
                address = _email_of(item)
                if address:
                    reasons.setdefault(address, reason)

        for items in (data.get("group_suppressions") or {}).values():
            for item in items or []:
                address = _email_of(item)
                if address:
                    reasons.setdefault(address, EmailSuppression.GROUP_UNSUBSCRIBE)

        before = EmailSuppression.objects.count()
        EmailSuppression.objects.bulk_create(
            [
                EmailSuppression(email=address, reason=reason)
                for address, reason in reasons.items()
            ],
            ignore_conflicts=True,
            batch_size=500,
        )
        created = EmailSuppression.objects.count() - before
        skipped = len(reasons) - created

        self.stdout.write(
            f"{created} created, {skipped} skipped (already present),"
            f" {len(reasons)} unique addresses.",
        )
