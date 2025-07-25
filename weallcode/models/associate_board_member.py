from django.db import models

from .common import CommonBoardMemberManager
from .common import CommonInfo


class AssociateBoardMember(CommonInfo):
    image = models.ImageField(
        upload_to="associate-board/",
        blank=True,
        null=True,
    )

    objects = CommonBoardMemberManager()

    def __str__(self):
        return self.name
