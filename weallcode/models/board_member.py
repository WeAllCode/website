from django.db import models

from .common import CommonBoardMemberManager, CommonInfo


class BoardMember(CommonInfo):
    image = models.ImageField(
        upload_to="board/",
        blank=True,
        null=True,
    )

    objects = CommonBoardMemberManager()

    def __str__(self):
        return self.name
