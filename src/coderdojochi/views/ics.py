import arrow
import calendar

from icalendar import Calendar, Event, vText

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View


class IcsView(View):
    event_type = None
    event_kwarg = None
    event_class = None

    def get_summary(self, request, event_obj):
        raise NotImplementedError

    def get_dtstart(self, request, event_obj):
        raise NotImplementedError

    def get_dtend(self, request, event_obj):
        raise NotImplementedError

    def get_description(self, request, event_obj):
        raise NotImplementedError

    def get(self, request, *args, **kwargs):
        event_obj = get_object_or_404(
            self.event_class,
            id=kwargs[self.event_kwarg]
        )
        cal = Calendar()

        cal['prodid'] = '-//CoderDojoChi//coderdojochi.org//'
        cal['version'] = '2.0'
        cal['calscale'] = 'GREGORIAN'

        event = Event()

        event['uid'] = u'{}{:04}@coderdojochi.org'.format(
            self.event_type.upper(), event_obj.id
        )
        event['summary'] = self.get_summary(request, event_obj)
        event['dtstart'] = self.get_dtstart(request, event_obj)
        event['dtend'] = self.get_dtend(request, event_obj)
        event['dtstamp'] = event['dtstart'][:-1]
        event['location'] = vText(event_obj.location.full)
        event['url'] = event_obj.get_absolute_url()
        event['description'] = self.get_description(request, event_obj)

        # A value of 5 is the normal or "MEDIUM" priority.
        # see: https://tools.ietf.org/html/rfc5545#section-3.8.1.9
        event['priority'] = 5

        cal.add_component(event)

        event_slug = u'coderdojochi-{}_{}'.format(
            self.event_type.lower(),
            arrow.get(
                event_obj.start_date
            ).to('local').format('MM-DD-YYYY_HH-mma')
        )

        # Return the ICS formatted calendar
        response = HttpResponse(
            cal.to_ical(),
            content_type='text/calendar',
            charset='utf-8'
        )

        response['Content-Disposition'] = u'attachment;filename={}.ics'.format(
            event_slug
        )

        return response
