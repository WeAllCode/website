from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from coderdojochi.factories import PartnerPasswordAccessFactory
from coderdojochi.factories import SessionFactory
from coderdojochi.models import Guardian
from coderdojochi.models import PartnerPasswordAccess

User = get_user_model()

SESSION_PASSWORD = "124"  # noqa: S105
USER_EMAIL = "email@email.com"
USER_PASSWORD = "pass123"  # noqa: S105


def _create_user(**extra):
    return User.objects.create_user(
        "user",
        email=USER_EMAIL,
        password=USER_PASSWORD,
        **extra,
    )


@override_settings(SECURE_SSL_REDIRECT=False)
class TestPartnerSessionPassword(TestCase):
    def setUp(self):
        self.partner_session = SessionFactory.create(password=SESSION_PASSWORD)
        self.url_kwargs = {"pk": self.partner_session.id}
        self.url = reverse("session-password", kwargs=self.url_kwargs)

    def test_session_password_invalid_password(self):
        response = self.client.post(self.url, data={"password": "abc"})
        self.assertContains(response, "Invalid password.")

    def test_session_password_no_password(self):
        response = self.client.post(self.url, data={"password": ""})
        self.assertContains(response, "Must enter a password.")

    def test_session_password_valid_password_unauthed(self):
        response = self.client.post(self.url, data={"password": SESSION_PASSWORD})

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == reverse("session-detail", kwargs=self.url_kwargs)
        assert PartnerPasswordAccess.objects.count() == 0
        # Anonymous visitors are remembered in their session instead.
        authed_sessions = self.client.session["authed_partner_sessions"]
        assert self.partner_session.id in authed_sessions

    def test_session_password_valid_password_authed(self):
        user = _create_user()
        assert self.client.login(email=USER_EMAIL, password=USER_PASSWORD)

        response = self.client.post(self.url, data={"password": SESSION_PASSWORD})

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == reverse("session-detail", kwargs=self.url_kwargs)
        assert PartnerPasswordAccess.objects.filter(
            session=self.partner_session,
            user=user,
        ).exists()
        authed_sessions = self.client.session["authed_partner_sessions"]
        assert self.partner_session.id in authed_sessions


@override_settings(SECURE_SSL_REDIRECT=False)
class TestSessionDetail(TestCase):
    def setUp(self):
        self.partner_session = SessionFactory.create(password=SESSION_PASSWORD)
        self.url_kwargs = {"pk": self.partner_session.id}
        self.url = reverse("session-detail", kwargs=self.url_kwargs)
        self.password_url = reverse("session-password", kwargs=self.url_kwargs)

    def test_redirect_password_unauthed(self):
        response = self.client.get(self.url)

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == self.password_url

    def test_redirect_password_authed(self):
        _create_user()
        assert self.client.login(email=USER_EMAIL, password=USER_PASSWORD)

        response = self.client.get(self.url)

        assert isinstance(response, HttpResponseRedirect)
        assert response.url == self.password_url

    def test_redirect_password_partner_password_access(self):
        user = _create_user(role="guardian")
        # The guardian detail page 404s without a Guardian profile.
        Guardian.objects.create(user=user)
        assert self.client.login(email=USER_EMAIL, password=USER_PASSWORD)
        PartnerPasswordAccessFactory.create(user=user, session=self.partner_session)

        response = self.client.get(self.url)

        assert getattr(response, "url", None) != self.password_url
        assert response.status_code == HTTPStatus.OK
