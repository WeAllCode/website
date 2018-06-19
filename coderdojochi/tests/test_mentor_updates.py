from unittest import TestCase

from django.test import TransactionTestCase

import mock

from coderdojochi.models import Mentor


class TestMentorAvatarUpdates(TransactionTestCase):
    @mock.patch('coderdojochi.signals_handlers.EmailMultiAlternatives')
    def test_new_mentor_no_avatar(self, mock_email):
        mentor = Mentor.objects.create()
        self.fail()

    # @mock.patch('coderdojochi.signals_handlers.EmailMultiAlternatives')
    # def test_new_mentor_no_avatar(self, mock_email):
    #     Mentor.objects.create()
