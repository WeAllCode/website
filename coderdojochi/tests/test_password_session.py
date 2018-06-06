# import mock
# import sys

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.test import Client
# from django.test import RequestFactory
from django.test import TestCase

# from coderdojochi.factories import CDCUserFactory
from coderdojochi.factories import PartnerPasswordAccessFactory
from coderdojochi.factories import SessionFactory
from coderdojochi.models import PartnerPasswordAccess
# from coderdojochi.views import session_detail


User = get_user_model()


class TestPartnerSessionPassword(TestCase):
    def setUp(self):
        self.partner_session = SessionFactory.create(password='124')
        self.url_kwargs = {
            'year': self.partner_session.start_date.year,
            'month': self.partner_session.start_date.month,
            'day': self.partner_session.start_date.day,
            'slug': self.partner_session.course.slug,
            'session_id': self.partner_session.id
        }
        self.client = Client()
        self.url = reverse('session_password', kwargs=self.url_kwargs)

    def test_session_password_invalid_password(self):
        response = self.client.post(self.url, data={'password': 'abc'})
        self.assertContains(response, 'Invalid password.')

    def test_session_password_no_password(self):
        response = self.client.post(self.url, data={'password': ''})
        self.assertContains(response, 'Must enter a password.')

    def test_session_password_valid_password_unauthed(self):
        response = self.client.post(
            self.url,
            data={
                'password': self.partner_session.password
            }
        )
        self.assertIsInstance(response, HttpResponseRedirect)

        detail_url = reverse('session_detail', kwargs=self.url_kwargs)
        self.assertEqual(response.url, detail_url)

        password_access_count = PartnerPasswordAccess.objects.count()
        self.assertEqual(password_access_count, 0)

        authed_sessions = self.client.session['authed_partner_sessions']
        self.assertFalse(str(self.partner_session.id) in authed_sessions)

    def test_session_password_valid_password_authed(self):
        user = User.objects.create_user(
            'user',
            email='email@email.com',
            password='pass123'
        )
        self.assertTrue(
            self.client.login(
                email='email@email.com',
                password='pass123'
            )
        )

        response = self.client.post(
            self.url,
            data={
                'password': self.partner_session.password
            }
        )
        self.assertIsInstance(response, HttpResponseRedirect)

        detail_url = reverse('session_detail', kwargs=self.url_kwargs)
        self.assertEqual(response.url, detail_url)

        partner_password_access = PartnerPasswordAccess.objects.get(
            session=self.partner_session,
            user=user
        )
        self.assertIsNotNone(partner_password_access)

        authed_sessions = self.client.session['authed_partner_sessions']
        self.assertTrue(str(self.partner_session.id) in authed_sessions)


class TestSessionDetail(TestCase):
    def setUp(self):
        super(TestSessionDetail, self).setUp()
        self.client = Client()
        self.partner_session = SessionFactory.create(password='124')
        self.url_kwargs = {
            'year': self.partner_session.start_date.year,
            'month': self.partner_session.start_date.month,
            'day': self.partner_session.start_date.day,
            'slug': self.partner_session.course.slug,
            'session_id': self.partner_session.id
        }
        self.url = reverse('session_detail', kwargs=self.url_kwargs)

    def test_redirect_password_unauthed(self):
        response = self.client.get(self.url)
        self.assertIsInstance(response, HttpResponseRedirect)

        detail_url = reverse('session_password', kwargs=self.url_kwargs)
        self.assertEqual(response.url, detail_url)

    def test_redirect_password_authed(self):
        User.objects.create_user(
            'user',
            email='email@email.com',
            password='pass123'
        )
        self.assertTrue(
            self.client.login(
                email='email@email.com',
                password='pass123'
            )
        )

        response = self.client.get(self.url)
        self.assertIsInstance(response, HttpResponseRedirect)

        detail_url = reverse('session_password', kwargs=self.url_kwargs)
        self.assertEqual(response.url, detail_url)

    def test_redirect_password_partner_password_access(self):
        user = User.objects.create_user(
            'user',
            email='email@email.com',
            password='pass123'
        )
        self.assertTrue(
            self.client.login(
                email='email@email.com',
                password='pass123'
            )
        )

        PartnerPasswordAccessFactory.create(
            user=user,
            session=self.partner_session
        )
        response = self.client.get(self.url)
        detail_url = reverse('session_password', kwargs=self.url_kwargs)

        # don't care what its doing as long as its not
        # redirecting to the password url.
        self.assertNotEqual(response.url, detail_url)
