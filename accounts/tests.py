import re
from http import HTTPStatus

from allauth.account.utils import user_display as allauth_user_display
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.core import mail
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from accounts.display import user_display
from coderdojochi.factories import CDCUserFactory
from coderdojochi.models import CDCUser
from coderdojochi.models import Guardian
from coderdojochi.models import Mentor
from coderdojochi.models import RaceEthnicity

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


class AccountNameRequiredTest(TestCase):
    """#847: a mentor or guardian could clear their name and save."""

    def setUp(self):
        self.race = RaceEthnicity.objects.create(
            race_ethnicity="Other",
            is_visible=True,
        )

    def _login(self, role):
        user = CDCUserFactory(
            first_name="Ada",
            last_name="Lovelace",
            email=f"{role}@example.com",
            role=role,
        )
        if role == "mentor":
            Mentor.objects.create(user=user)
        else:
            Guardian.objects.create(user=user)
        self.client.force_login(user)
        return user

    def _data(self, role, **overrides):
        data = {
            "first_name": "Grace",
            "last_name": "Hopper",
            "gender": "Female",
            "race_ethnicity": [self.race.pk],
            "birthday": "1990-01-02",
            "phone": "312-555-0100",
        }
        if role == "guardian":
            data["zip"] = "60601"
        data.update(overrides)
        return data

    def _post(self, role, **overrides):
        return self.client.post(
            reverse("account_home"),
            self._data(role, **overrides),
            secure=True,
        )

    def test_empty_name_is_rejected(self):
        for role in ("mentor", "guardian"):
            for field in ("first_name", "last_name"):
                with self.subTest(role=role, field=field):
                    user = self._login(role)
                    response = self._post(role, **{field: ""})
                    assert response.status_code == HTTPStatus.OK
                    assert field in response.context["user_form"].errors
                    user.refresh_from_db()
                    assert (user.first_name, user.last_name) == ("Ada", "Lovelace")
                    assert len(mail.outbox) == 0
                    user.delete()

    def test_valid_post_saves(self):
        for role in ("mentor", "guardian"):
            with self.subTest(role=role):
                user = self._login(role)
                response = self._post(role)
                assert response.status_code == HTTPStatus.FOUND
                user.refresh_from_db()
                assert (user.first_name, user.last_name) == ("Grace", "Hopper")
                user.delete()
