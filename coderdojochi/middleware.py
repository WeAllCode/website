"""Cache-Control headers for Cloudflare's edge cache.

Cloudflare respects origin headers, so this middleware decides what may be
cached: allowlisted public pages for logged-out visitors get a short shared
TTL (s-maxage), and everything else is stamped private so Cloudflare never
falls back to its default HTML TTLs.
"""

from django.conf import settings
from django.utils.cache import patch_cache_control

# Pages whose HTML is the same for every logged-out visitor. Not
# weallcode-join-us (form + csrf cookie) and not session-detail (password
# redirect; not yet checked for per-request content).
PUBLIC_CACHE_VIEW_NAMES = frozenset(
    {
        "weallcode-home",
        "weallcode-our-story",
        "weallcode-programs",
        "weallcode-programs-summer-camps",
        "weallcode-team",
        "weallcode-associate-board",
        "weallcode-privacy",
        "weallcode-credits",
        "mentors",
        "mentor-detail",
    }
)

MESSAGES_COOKIE_NAME = "messages"


def _is_publicly_cacheable(request, response, seconds):  # noqa: PLR0911
    # One early return per guard, so each can be tested (and mutated) alone.
    if seconds <= 0:
        # Kill switch.
        return False
    if request.method not in ("GET", "HEAD"):
        return False
    if response.status_code != 200:
        # Redirects, 404s and errors would otherwise get Cloudflare defaults.
        return False
    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match is None:
        return False
    if resolver_match.view_name not in PUBLIC_CACHE_VIEW_NAMES:
        return False
    user = getattr(request, "user", None)
    if user is None:
        return False
    if user.is_authenticated:
        # Logged-in pages differ per user (header, mentor content).
        return False
    if response.cookies:
        # A response that sets a cookie must never be shared.
        return False
    if settings.SESSION_COOKIE_NAME in request.COOKIES:
        return False
    if MESSAGES_COOKIE_NAME in request.COOKIES:
        # A flash message is waiting to be rendered.
        return False
    return True


def public_cache_headers(get_response):
    def middleware(request):
        response = get_response(request)

        # Respect views that set their own policy (e.g. never_cache).
        if response.has_header("Cache-Control"):
            return response

        # Read per request so override_settings and the kill switch take effect.
        seconds = settings.PUBLIC_CACHE_SECONDS
        if _is_publicly_cacheable(request, response, seconds):
            patch_cache_control(
                response,
                public=True,
                max_age=0,
                s_maxage=seconds,
            )
        else:
            patch_cache_control(response, private=True)
        return response

    return middleware
