from django.contrib import sitemaps
from django.urls import reverse
from django.utils import timezone


class StaticSitemapView(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return [
            "weallcode-home",
            "weallcode-our-story",
            "weallcode-programs",
            "weallcode-programs-summer-camps",
            "weallcode-team",
            "weallcode-join-us",
            "weallcode-privacy",
            "weallcode-credits",
        ]

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return timezone.now()
