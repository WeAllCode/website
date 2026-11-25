from http import HTTPStatus

from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.test import RequestFactory
from django.test import TestCase
from django.test import override_settings
from django.urls import resolve
from django.urls import reverse

from coderdojochi.middleware import PUBLIC_CACHE_VIEW_NAMES
from coderdojochi.middleware import public_cache_headers


def _directives(response):
    return {d.strip() for d in response["Cache-Control"].split(",") if d.strip()}


def _make_user():
    return get_user_model().objects.create_user(
        username="ada",
        email="ada@example.com",
        first_name="Ada",
        last_name="Lovelace",
    )


@override_settings(SECURE_SSL_REDIRECT=False)
class CacheHeadersClientTest(TestCase):
    def assert_private(self, response):
        directives = _directives(response)
        assert "private" in directives, directives
        assert "public" not in directives, directives

    def test_allowlist_names_resolve(self):
        for name in PUBLIC_CACHE_VIEW_NAMES - {"mentor-detail"}:
            reverse(name)
        reverse("mentor-detail", kwargs={"pk": 1})

    def test_anonymous_home_is_public(self):
        response = self.client.get("/")

        assert response.status_code == HTTPStatus.OK
        directives = _directives(response)
        assert "public" in directives, directives
        assert "s-maxage=60" in directives, directives
        assert "max-age=0" in directives, directives

    def test_logged_in_home_is_private(self):
        self.client.force_login(_make_user())

        response = self.client.get("/")

        assert response.status_code == HTTPStatus.OK
        self.assert_private(response)

    def test_join_us_is_private(self):
        response = self.client.get("/join-us/")

        assert response.status_code == HTTPStatus.OK
        assert "csrftoken" in response.cookies
        self.assert_private(response)

    def test_login_page_not_public(self):
        # The login template renders the Google button, which needs a SocialApp.
        app = SocialApp.objects.create(
            provider="google",
            name="google",
            client_id="google-id",
            secret="google-secret",  # noqa: S106
        )
        app.sites.add(Site.objects.get_current())

        response = self.client.get("/account/login/")

        assert response.status_code == HTTPStatus.OK
        assert "public" not in _directives(response)

    def test_404_is_private(self):
        response = self.client.get("/no-such-page-xyz/")

        assert response.status_code == HTTPStatus.NOT_FOUND
        self.assert_private(response)

    def test_allowlisted_404_is_private(self):
        # Resolves to mentor-detail, so resolver_match is set; only the
        # status-code guard keeps this 404 from being marked public.
        response = self.client.get("/mentors/999999/")

        assert response.status_code == HTTPStatus.NOT_FOUND
        self.assert_private(response)

    def test_messages_cookie_is_private(self):
        # A fake messages cookie fails to decode, so Django deletes it in the
        # response too; this proves the behaviour, not the request-cookie line
        # on its own (accepted in the plan).
        self.client.cookies["messages"] = "x"

        response = self.client.get("/")

        assert response.status_code == HTTPStatus.OK
        self.assert_private(response)

    @override_settings(PUBLIC_CACHE_SECONDS=0)
    def test_kill_switch(self):
        response = self.client.get("/")

        assert response.status_code == HTTPStatus.OK
        self.assert_private(response)

    def test_redirect_is_private(self):
        response = self.client.get("/get-involved/")

        assert response.status_code == HTTPStatus.FOUND
        self.assert_private(response)


@override_settings(SECURE_SSL_REDIRECT=False)
class CacheHeadersGuardTest(TestCase):
    """Each guard alone, via a direct middleware call on a home-page request."""

    def _call(self, user, *, cookies=None, set_cookie=False):
        request = RequestFactory().get("/")
        request.resolver_match = resolve("/")
        request.user = user
        request.COOKIES = dict(cookies or {})

        def get_response(_request):
            response = HttpResponse(status=HTTPStatus.OK)
            if set_cookie:
                response.set_cookie("x", "y")
            return response

        return _directives(public_cache_headers(get_response)(request))

    def test_guard_control_anonymous_is_public(self):
        directives = self._call(AnonymousUser())

        assert "public" in directives, directives
        assert "s-maxage=60" in directives, directives
        assert "max-age=0" in directives, directives

    def test_guard_authenticated_no_cookie(self):
        directives = self._call(_make_user())

        assert "private" in directives, directives
        assert "public" not in directives, directives

    def test_guard_request_sessionid(self):
        directives = self._call(AnonymousUser(), cookies={"sessionid": "x"})

        assert "private" in directives, directives
        assert "public" not in directives, directives

    def test_guard_response_cookie(self):
        directives = self._call(AnonymousUser(), set_cookie=True)

        assert "private" in directives, directives
        assert "public" not in directives, directives
