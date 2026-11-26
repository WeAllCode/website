from email.utils import getaddresses
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.test import override_settings

from weallcode.forms import ContactForm

CONTACT_EMAIL = "staff@example.com"


# Django's test runner swaps in locmem; anymail's test backend parses addresses
# the way the Resend backend does on prod.
@override_settings(
    CONTACT_EMAIL=CONTACT_EMAIL,
    EMAIL_BACKEND="anymail.backends.test.EmailBackend",
)
class ContactFormEmailTest(TestCase):
    def send(self, name, address):
        form = ContactForm()
        form.cleaned_data = {
            "name": name,
            "email": address,
            "interest": "volunteer",
            "phone": "+1 555 555-5555",
            "message": "Hello, I would like to help out with classes.",
        }
        with mock.patch("coderdojochi.util.time.sleep"):
            form.send_email()
        assert len(mail.outbox) == 1, "contact email was not sent"
        return mail.outbox[0]

    def assert_reply_to(self, name, address):
        msg = self.send(name, address)
        assert msg.to == [CONTACT_EMAIL]
        assert getaddresses(msg.reply_to) == [(name, address)]
        # What anymail parsed and would hand to Resend.
        sent = msg.anymail_test_params["reply_to"]
        assert [(e.display_name, e.addr_spec) for e in sent] == [(name, address)]

    def test_reply_to_plain_name(self):
        self.assert_reply_to("Ada Lovelace", "ada@example.com")

    def test_reply_to_name_with_parentheses(self):
        self.assert_reply_to("Ali (test)", "ali@example.com")

    def test_reply_to_name_with_comma_in_parentheses(self):
        # The name that failed on prod on 2026-11-25.
        self.assert_reply_to("Ali Karbassi (test, please ignore)", "ali@example.com")

    def test_reply_to_name_with_apostrophe_and_comma(self):
        self.assert_reply_to("O'Brien, Pat", "pat@example.com")

    def test_reply_to_name_with_quotes_and_angle_bracket(self):
        self.assert_reply_to('Sam "<Sammy>" Lee', "sam@example.com")

    def test_from_email_parses(self):
        msg = self.send("Ada Lovelace", "ada@example.com")
        assert getaddresses([msg.from_email])[0][0] == "We All Code"


@override_settings(
    SECURE_SSL_REDIRECT=False, SENTRY_DSN="https://public@example.invalid/1"
)
class NotFoundPageTest(TestCase):
    def test_missing_page_renders_404_template(self):
        with mock.patch("sentry_sdk.scope.Scope.capture_message") as capture:
            response = self.client.get("/this-page-does-not-exist/")
        assert response.status_code == 404
        self.assertTemplateUsed(response, "404.html")
        self.assertContains(response, "Missing Page", status_code=404)
        capture.assert_not_called()
