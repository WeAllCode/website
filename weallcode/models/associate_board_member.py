from collections import defaultdict
from itertools import chain

from django.db import models

from .common import CommonBoardMemberManager, CommonInfo


class AssociateBoardMember(CommonInfo):

    image = models.ImageField(
        upload_to="associate-board/",
        blank=True,
        null=True,
    )

    objects = CommonBoardMemberManager()

    def __str__(self):
        return self.name
