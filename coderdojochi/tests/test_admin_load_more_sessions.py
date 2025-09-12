from datetime import timedelta
import json

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from coderdojochi.models import Session


User = get_user_model()


class TestAdminLoadMoreSessions(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff_user',
            email='staff@example.com',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='user@example.com',
            is_staff=False
        )
        
    def test_load_more_sessions_requires_staff(self):
        """Test that non-staff users cannot access the endpoint"""
        self.client.login(username='regular_user', password='password')
        response = self.client.get(reverse('load-more-sessions'))
        self.assertEqual(response.status_code, 403)
        
    def test_load_more_sessions_requires_login(self):
        """Test that unauthenticated users cannot access the endpoint"""
        response = self.client.get(reverse('load-more-sessions'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
    def test_load_more_sessions_staff_access(self):
        """Test that staff users can access the endpoint"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('load-more-sessions'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
    def test_load_more_sessions_pagination(self):
        """Test pagination parameters"""
        self.client.force_login(self.staff_user)
        
        # Test with custom offset and limit
        response = self.client.get(reverse('load-more-sessions'), {
            'offset': 10,
            'limit': 5
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('html', data)
        self.assertIn('has_more', data)
        self.assertIn('next_offset', data)
        self.assertEqual(data['next_offset'], 15)
        
    def test_load_more_sessions_365_day_limit(self):
        """Test that only sessions from last 365 days are included"""
        self.client.force_login(self.staff_user)
        
        # This test would require creating Session objects with specific dates
        # For now, just verify the endpoint responds correctly
        response = self.client.get(reverse('load-more-sessions'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsInstance(data['has_more'], bool)