from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

import arrow
from icalendar import (
    Calendar,
    Event,
    vText,
)


class CalendarView(View):
    event_type = None
    event_kwarg = "pk"
    event_class = None

    def get_summary(self, request, event_obj):
        raise NotImplementedError

    def get_dtstart(self, request, event_obj):
        raise NotImplementedError

    def get_dtend(self, request, event_obj):
        raise NotImplementedError

    def get_description(self, event_obj):
        raise NotImplementedError

    def get_location(self, request, event_obj):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        event_obj = get_object_or_404(
            self.event_class, id=kwargs[self.event_kwarg]
        )
        cal = Calendar()

        cal["prodid"] = "-//We All Code//weallcode.org//"
        cal["version"] = "2.0"
        cal["calscale"] = "GREGORIAN"

        event = Event()

        event["uid"] = (
            f"{self.event_type.upper()}{event_obj.id:04}@weallcode.org"
        )
        event["summary"] = self.get_summary(request, event_obj)
        event["dtstart"] = self.get_dtstart(request, event_obj)
        event["dtend"] = self.get_dtend(request, event_obj)
        event["dtstamp"] = event["dtstart"][:-1]
        event["location"] = vText(self.get_location(request, event_obj))
        event["url"] = f"{settings.SITE_URL}{event_obj.get_absolute_url()}"
        event["description"] = self.get_description(event_obj)

        # A value of 5 is the normal or "MEDIUM" priority.
        # see: https://tools.ietf.org/html/rfc5545#section-3.8.1.9
        event["priority"] = 5

        cal.add_component(event)

        event_slug = "weallcode-{event_type}_{date}".format(
            event_type=self.event_type.lower(),
            date=arrow.get(event_obj.start_date)
            .to("local")
            .format("MM-DD-YYYY_HH-mma"),
        )

        # Return the ICS formatted calendar
        response = HttpResponse(
            cal.to_ical(), content_type="text/calendar", charset="utf-8"
        )

        response["Content-Disposition"] = (
            f"attachment;filename={event_slug}.ics"
        )

        return response
