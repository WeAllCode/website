from unittest import mock

from django.test import TransactionTestCase

from coderdojochi.models import Mentor


class TestMentorAvatarUpdates(TransactionTestCase):
    @mock.patch("coderdojochi.signals_handlers.EmailMultiAlternatives")
    def test_new_mentor_no_avatar(self, mock_email):
        Mentor.objects.create()
        self.fail()

    # @mock.patch('coderdojochi.signals_handlers.EmailMultiAlternatives')
    # def test_new_mentor_no_avatar(self, mock_email):
    #     Mentor.objects.create()
