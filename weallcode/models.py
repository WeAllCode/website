from django.db import models

CHAIR = "Chair"
VICE_CHAIR = "Vice Chair"
SECRETARY = "Secretary"
TREASURER = "Treasurer"
DIRECTOR = "Director"
PRESIDENT = "President"

ROLE_CHOICES = [
    (CHAIR, "Chair"),
    (VICE_CHAIR, "Vice Chair"),
    (SECRETARY, "Secretary"),
    (TREASURER, "Treasurer"),
    (DIRECTOR, "Director"),
    (PRESIDENT, "President"),
]


class CommonInfo(models.Model):

    name = models.CharField(max_length=255,)

    role = models.CharField(choices=ROLE_CHOICES, max_length=255, default=DIRECTOR,)

    image = models.ImageField(upload_to="staff/", blank=True, null=True,)

    description = models.CharField(max_length=255, blank=True, null=True,)

    linkedin = models.URLField(max_length=200, blank=True, null=True,)

    # Active
    is_active = models.BooleanField(default=True,)

    # Auto create/update
    created_at = models.DateTimeField(auto_now_add=True,)

    updated_at = models.DateTimeField(auto_now=True,)

    class Meta:
        abstract = True


class StaffMember(CommonInfo):

    role = models.CharField(max_length=255,)

    image = models.ImageField(upload_to="staff/", blank=True, null=True,)

    def __str__(self):
        return self.name


class BoardMember(CommonInfo):

    image = models.ImageField(upload_to="board/", blank=True, null=True,)

    def __str__(self):
        return self.name


class AssociateBoardMember(CommonInfo):

    image = models.ImageField(upload_to="associate-board/", blank=True, null=True,)

    def __str__(self):
        return self.name
