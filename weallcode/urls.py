from django.conf.urls import include
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.views.generic import RedirectView

from weallcode.views import (
    AssociateBoardView,
    CreditsView,
    HomeView,
    JoinUsView,
    OurStoryView,
    PrivacyView,
    ProgramsSummerCampsView,
    ProgramsView,
    StaticSitemapView,
    TeamView,
)

sitemaps = {
    "static": StaticSitemapView,
}

urlpatterns = [
    path("", HomeView.as_view(), name="weallcode-home"),
    path("our-story/", OurStoryView.as_view(), name="weallcode-our-story"),
    path(
        "programs/",
        include(
            [
                path("", ProgramsView.as_view(), name="weallcode-programs"),
                path(
                    "summer-camps/",
                    ProgramsSummerCampsView.as_view(),
                    name="weallcode-programs-summer-camps",
                ),
            ]
        ),
    ),
    path("team/", TeamView.as_view(), name="weallcode-team"),
    path(
        "join-us/",
        include(
            [
                path("", JoinUsView.as_view(), name="weallcode-join-us"),
                path(
                    "associate-board/",
                    AssociateBoardView.as_view(),
                    name="weallcode-associate-board",
                ),
            ]
        ),
    ),
    path("privacy/", PrivacyView.as_view(), name="weallcode-privacy"),
    path("credits/", CreditsView.as_view(), name="weallcode-credits"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    # Redirect /summer-camps/ to weallcode-programs-summer-camps
    path(
        "summer-camps/",
        RedirectView.as_view(pattern_name="weallcode-programs-summer-camps"),
    ),
    # Redirect /get-involved/ to weallcode-join-us
    path(
        "get-involved/", RedirectView.as_view(pattern_name="weallcode-join-us")
    ),
]

handler404 = "weallcode.views.page_not_found_view"


# Sentry Testing
def trigger_error(request):
    1 / 0  # Intentional division by zero for Sentry testing


urlpatterns += [
    path("test--sentry/", trigger_error),
]
