from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse


@override_settings(SECURE_SSL_REDIRECT=False)
class AdminDashboardTest(TestCase):
    def test_no_checked_in_orders(self):
        # Sentry PRODUCTION-43J: ZeroDivisionError averaging an empty age list.
        staff = get_user_model().objects.create_user(
            username="staff",
            email="staff@example.com",
            is_staff=True,
        )
        self.client.force_login(staff)
        response = self.client.get(reverse("cdc-admin"))
        assert response.status_code == 200
        assert response.context["average_age"] == 0
