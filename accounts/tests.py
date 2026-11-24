import re
from http import HTTPStatus

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.test import Client
from django.test import TestCase

GOOGLE_FORM = re.compile(
    r'<form method="post" action="(?P<action>/account/google/login/[^"]*)"'
    r' class="social-login-form">\s*'
    r'<input type="hidden" name="csrfmiddlewaretoken" value="(?P<token>[^"]+)">',
)


class SocialLoginPostTest(TestCase):
    """allauth 65 shows a confirm page on GET, so the buttons must POST."""

    def setUp(self):
        site = Site.objects.get_current()
        for provider in ("google", "facebook"):
            app = SocialApp.objects.create(
                provider=provider,
                name=provider,
                client_id=f"{provider}-id",
                secret=f"{provider}-secret",
            )
            app.sites.add(site)
        self.client = Client(enforce_csrf_checks=True)

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
