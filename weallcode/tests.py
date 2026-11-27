import re
from email.utils import getaddresses
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core import mail
from django.template import Context
from django.template import Template
from django.test import RequestFactory
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from coderdojochi.middleware import PUBLIC_CACHE_VIEW_NAMES
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


class NavCurrentTest(TestCase):
    """Only the current section's header link gets aria-current="page"."""

    @staticmethod
    def render(path):
        request = RequestFactory().get(path)
        return Template(
            "{% load nav %}<a{% nav_current 'weallcode-programs' %}>"
        ).render(Context({"request": request}))

    def test_home_marks_nothing(self):
        assert self.render("/") == "<a>"

    def test_section_and_subpage_are_current(self):
        assert self.render("/programs/") == '<a aria-current="page">'
        assert self.render("/programs/summer-camps/") == '<a aria-current="page">'

    def test_other_section_is_not_current(self):
        assert self.render("/team/") == "<a>"


def rewrite_paths(hcl):
    """The `http.request.uri.path in {...}` set of a Transform Rule expression."""
    match = re.search(r"http\.request\.uri\.path in \{([^}]*)\}", hcl)
    assert match, "no http.request.uri.path in {...} clause"
    values = re.findall(r'"([^"]*)"', match.group(1).replace('\\"', '"'))
    return {v for v in values if v.startswith("/")}


@override_settings(SECURE_SSL_REDIRECT=False)
class EdgeQueryStripTest(TestCase):
    """The edge strips query strings on cached pages (infra/terraform/transform.tf)."""

    def test_canonical_drops_query(self):
        response = self.client.get("/?utm_source=x")
        assert response.status_code == 200
        canonical = re.search(
            r'<link rel="canonical" href="([^"]*)" />', response.content.decode()
        )
        assert canonical, "no canonical link"
        assert canonical.group(1).endswith("://" + settings.META_SITE_DOMAIN + "/")
        self.assertNotContains(response, "utm_source")

    def test_rewrite_paths_match_allowlist(self):
        hcl = (Path(settings.BASE_DIR) / "infra/terraform/transform.tf").read_text()
        expected = {reverse(n) for n in PUBLIC_CACHE_VIEW_NAMES - {"mentor-detail"}}
        assert rewrite_paths(hcl) == expected
        assert reverse("mentor-detail", kwargs={"pk": 1}).startswith("/mentors/")
