import json
import mimetypes
from io import BytesIO
from unittest import mock

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from PIL import Image

from coderdojochi.models import Mentor


def _image(color, name="avatar.png", image_format="PNG"):
    buffer = BytesIO()
    Image.new("RGB", (1, 1), color).save(buffer, format=image_format)
    content_type = f"image/{image_format.lower()}"
    return SimpleUploadedFile(name, buffer.getvalue(), content_type)


def _png(color):
    return _image(color)


def _resend_ok(*args, **kwargs):
    response = requests.Response()
    response.status_code = 200
    response.headers["Content-Type"] = "application/json"
    response.raw = BytesIO(b'{"id": "x"}')
    response.encoding = "utf-8"
    return response


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
        assert attachment.get_content_disposition() == "inline"
        assert attachment.get_filename() == "avatar.png"
        assert mimetypes.guess_type(attachment.get_filename())[0] == "image/png"
        assert mentor.avatar_approved is False

    @mock.patch("coderdojochi.signals_handlers.email")
    def test_changed_jpeg_avatar_filename_matches_type(self, mock_email):
        mentor = Mentor.objects.create(user=self.user)
        mentor.avatar = _image("blue", name="Avatar.JPG", image_format="JPEG")
        mentor.save()

        (attachment,) = mock_email.call_args.kwargs["attachments"]
        assert attachment.get_content_type() == "image/jpeg"
        filename = attachment.get_filename()
        assert filename.endswith((".jpg", ".jpeg"))
        assert mimetypes.guess_type(filename)[0] == "image/jpeg"

    @mock.patch("coderdojochi.signals_handlers.email")
    def test_avatar_without_extension_sniffs_type(self, mock_email):
        mentor = Mentor.objects.create(user=self.user)
        mentor.avatar = _image("green", name="avatar")
        mentor.save()

        (attachment,) = mock_email.call_args.kwargs["attachments"]
        assert attachment.get_content_type() == "image/png"
        assert attachment.get_filename() == "avatar.png"

    @override_settings(
        EMAIL_BACKEND="anymail.backends.resend.EmailBackend",
        ANYMAIL={"RESEND_API_KEY": "test"},
    )
    @mock.patch("requests.Session.request", side_effect=_resend_ok)
    def test_changed_avatar_sends_through_resend_backend(self, mock_request):
        mentor = Mentor.objects.create(user=self.user)
        mentor.avatar = _png("red")
        # util._send swallows send errors, so a logged error is the failure signal.
        with self.assertNoLogs("coderdojochi.util", "ERROR"):
            mentor.save()

        mock_request.assert_called_once()
        payload = json.loads(mock_request.call_args.kwargs["data"])
        assert "cid:avatar" in payload["html"]
        (attachment,) = payload["attachments"]
        assert attachment["filename"] == "avatar.png"
        assert attachment["content_type"] == "image/png"
        assert attachment["content_id"] == "avatar"
