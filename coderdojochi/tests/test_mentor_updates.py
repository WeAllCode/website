from io import BytesIO
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from coderdojochi.models import Mentor


def _png(color):
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color).save(buffer, format="PNG")
    return SimpleUploadedFile("avatar.png", buffer.getvalue(), "image/png")


class TestMentorAvatarUpdates(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="ada",
            email="ada@example.com",
            first_name="Ada",
            last_name="Lovelace",
        )

    @mock.patch("coderdojochi.signals_handlers.email")
    def test_new_mentor_no_avatar(self, mock_email):
        Mentor.objects.create(user=self.user)

        mock_email.assert_not_called()

    @mock.patch("coderdojochi.signals_handlers.email")
    def test_changed_avatar_emails_for_approval(self, mock_email):
        mentor = Mentor.objects.create(user=self.user)
        mentor.avatar_approved = True
        mentor.avatar = _png("red")
        mentor.save()

        mock_email.assert_called_once()
        kwargs = mock_email.call_args.kwargs
        assert kwargs["subject"] == "Ada Lovelace | Mentor Avatar Changed"
        assert kwargs["template_name"] == "avatar_changed_mentor"
        assert kwargs["recipients"] == [settings.CONTACT_EMAIL]
        assert kwargs["preheader"] == "Mentor Avatar Changed"
        assert kwargs["mixed_subtype"] == "related"
        assert kwargs["merge_global_data"]["first_name"] == "Ada"
        assert kwargs["merge_global_data"]["approve_url"].endswith(
            mentor.get_approve_avatar_url(),
        )
        assert kwargs["merge_global_data"]["reject_url"].endswith(
            mentor.get_reject_avatar_url(),
        )
        (attachment,) = kwargs["attachments"]
        assert attachment["Content-Id"] == "avatar"
        assert attachment.get_content_type() == "image/png"
        assert mentor.avatar_approved is False
