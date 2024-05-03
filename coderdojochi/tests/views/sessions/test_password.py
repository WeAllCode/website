from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from coderdojochi.models import Session
from coderdojochi.views.sessions.password import PasswordSessionView

class TestPasswordSessionView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.session = Session.objects.create(
            title="Test Session",
            description="This is a test session.",
            start_date="2021-10-10 10:00:00",
            end_date="2021-10-10 12:00:00",
            password="testpassword"
        )
        self.url = reverse('session_password', kwargs={'pk': self.session.pk})

    def test_password_session_view_redirects_for_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_password_session_view_renders_for_authenticated_user(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sessions/password.html')

    def test_password_session_view_invalid_password(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(self.url, {'password': 'wrongpassword'})
        self.assertFormError(response, 'form', 'password', 'Invalid password.')

    def test_password_session_view_valid_password(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(self.url, {'password': 'testpassword'})
        self.assertRedirects(response, reverse('session_detail', kwargs={'pk': self.session.pk}))
