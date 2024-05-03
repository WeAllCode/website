from django.test import TestCase
from django.urls import reverse
from coderdojochi.factories import SessionFactory, GuardianFactory, StudentFactory
from coderdojochi.models import Order

class TestSessionSignUpView(TestCase):
    def setUp(self):
        self.session = SessionFactory()
        self.guardian = GuardianFactory()
        self.student = StudentFactory(guardian=self.guardian)
        self.url = reverse('session-sign-up', kwargs={'pk': self.session.pk})

    def test_signup_view_redirects_when_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_signup_view_renders_when_logged_in(self):
        self.client.force_login(self.guardian.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sessions/signup.html')

    def test_successful_signup_creates_order(self):
        self.client.force_login(self.guardian.user)
        response = self.client.post(self.url, {'student_id': self.student.id})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(session=self.session, student=self.student).exists())
