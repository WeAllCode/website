from django.test import TestCase
from django.urls import reverse

from coderdojochi.models import Session
from coderdojochi.factories import SessionFactory


class SessionDetailViewTest(TestCase):
    def setUp(self):
        self.session = SessionFactory()
        self.url = reverse('session_detail', kwargs={'pk': self.session.pk})

    def test_session_detail_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_session_detail_view_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'session_detail.html')

    def test_session_detail_view_context_data(self):
        response = self.client.get(self.url)
        self.assertTrue('session' in response.context)
        self.assertEqual(response.context['session'], self.session)
