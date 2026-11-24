from django.core import signing
from django.shortcuts import render
from django.views import View

from coderdojochi.models import EmailSuppression
from coderdojochi.util import unsubscribe_email_from_token


class UnsubscribeView(View):
    """GET only shows a confirm button, so link scanners can't unsubscribe anyone.

    POST adds the suppression.
    """

    template_name = "unsubscribe.html"

    def _email_or_none(self, token):
        try:
            return unsubscribe_email_from_token(token)
        except signing.BadSignature:
            return None

    def _invalid(self, request):
        return render(request, self.template_name, {"invalid": True}, status=400)

    def get(self, request, token):
        email_address = self._email_or_none(token)
        if email_address is None:
            return self._invalid(request)
        return render(request, self.template_name, {"email": email_address})

    def post(self, request, token):
        email_address = self._email_or_none(token)
        if email_address is None:
            return self._invalid(request)
        EmailSuppression.objects.get_or_create(
            email=email_address.strip().lower(),
            defaults={"reason": EmailSuppression.USER_UNSUBSCRIBE},
        )
        return render(
            request, self.template_name, {"email": email_address, "unsubscribed": True}
        )
