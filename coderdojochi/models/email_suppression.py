from django.db import models


class EmailSuppression(models.Model):
    """An address that must never receive mail from `coderdojochi.util.email`."""

    UNSUBSCRIBE = "unsubscribe"
    BOUNCE = "bounce"
    BLOCK = "block"
    SPAM_REPORT = "spam_report"
    GROUP_UNSUBSCRIBE = "group_unsubscribe"
    USER_UNSUBSCRIBE = "user_unsubscribe"

    REASON_CHOICES = [
        (UNSUBSCRIBE, "Unsubscribe (SendGrid)"),
        (BOUNCE, "Bounce (SendGrid)"),
        (BLOCK, "Block (SendGrid)"),
        (SPAM_REPORT, "Spam report (SendGrid)"),
        (GROUP_UNSUBSCRIBE, "Group unsubscribe (SendGrid)"),
        (USER_UNSUBSCRIBE, "Unsubscribed via link"),
    ]

    email = models.EmailField(unique=True)
    reason = models.CharField(max_length=32, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "email suppression"
        verbose_name_plural = "email suppressions"

    def __str__(self):
        return f"{self.email} ({self.reason})"

    def save(self, *args, **kwargs):
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)
