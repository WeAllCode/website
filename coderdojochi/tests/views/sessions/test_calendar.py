from django.test import TestCase
from django.urls import reverse
from coderdojochi.factories import SessionFactory
from coderdojochi.models import Session

class SessionCalendarViewTest(TestCase):
    def setUp(self):
        self.session = SessionFactory()
        self.url = reverse('session_calendar', kwargs={'pk': self.session.pk})

    def test_calendar_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_calendar_view_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'sessions/calendar.html')

    def test_calendar_view_context_data(self):
        response = self.client.get(self.url)
        self.assertTrue('session' in response.context)
        self.assertEqual(response.context['session'], self.session)
