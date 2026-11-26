import re
from http import HTTPStatus

from allauth.account.utils import user_display as allauth_user_display
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from accounts.display import user_display
from coderdojochi.factories import CDCUserFactory
from coderdojochi.models import CDCUser

GOOGLE_FORM = re.compile(
    r'<form method="post" action="(?P<action>/account/google/login/[^"]*)"'
    r' class="social-login-form">\s*'
    r'<input type="hidden" name="csrfmiddlewaretoken" value="(?P<token>[^"]+)">',
)


class SocialLoginPostTest(TestCase):
    """allauth 65 shows a confirm page on GET, so the buttons must POST."""

    def setUp(self):
        app = SocialApp.objects.create(
            provider="google",
            name="google",
            client_id="google-id",
            secret="google-secret",  # noqa: S106
        )
        app.sites.add(Site.objects.get_current())
        self.client = Client(enforce_csrf_checks=True)

    def test_no_facebook_login_on_login_or_signup(self):
        """Meta disabled our Facebook app, so the buttons are gone."""
        for path in ("/account/login/", "/account/signup/"):
            response = self.client.get(path, secure=True)
            assert response.status_code == HTTPStatus.OK
            assert "/account/facebook/login/" not in response.content.decode()

    def test_login_page_posts_to_google_with_next(self):
        response = self.client.get("/account/login/?next=/account/", secure=True)
        assert response.status_code == HTTPStatus.OK
        match = GOOGLE_FORM.search(response.content.decode())
        assert match, "no POST form with csrf token targeting google login"
        assert match["action"] == "/account/google/login/?next=%2Faccount%2F"

    def test_post_redirects_straight_to_google(self):
        page = self.client.get("/account/login/?next=/account/", secure=True)
        match = GOOGLE_FORM.search(page.content.decode())
        assert match
        response = self.client.post(
            match["action"],
            {"csrfmiddlewaretoken": match["token"]},
            secure=True,
            HTTP_REFERER="https://testserver/account/login/",
        )
        assert response.status_code == HTTPStatus.FOUND
        assert response["Location"].startswith(
            "https://accounts.google.com/",
        ), response["Location"]


class AccountHomeUnknownRoleTest(TestCase):
    """A role that is neither mentor nor guardian redirects, not a 500."""

    def setUp(self):
        user = CDCUserFactory()
        CDCUser.objects.filter(pk=user.pk).update(role="bogus")
        user.refresh_from_db()
        self.client.force_login(user)

    def test_get_redirects_to_welcome(self):
        response = self.client.get(reverse("account_home"), secure=True)
        assert response.status_code == HTTPStatus.FOUND
        assert response["Location"] == reverse("welcome")

    def test_post_redirects_to_welcome(self):
        response = self.client.post(reverse("account_home"), {}, secure=True)
        assert response.status_code == HTTPStatus.FOUND
        assert response["Location"] == reverse("welcome")


class UserDisplayTest(TestCase):
    # #846: allauth showed the generated username on screens and in emails.
    def test_full_name(self):
        user = CDCUserFactory(
            first_name="Ada", last_name="Lovelace", email="ada@example.com"
        )
        assert user_display(user) == "Ada Lovelace"

    def test_falls_back_to_email(self):
        user = CDCUserFactory(email="ada@example.com")
        assert user_display(user) == "ada@example.com"

    def test_allauth_uses_it(self):
        user = CDCUserFactory(first_name="Ada", last_name="Lovelace")
        assert allauth_user_display(user) == "Ada Lovelace"
