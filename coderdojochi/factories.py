from datetime import UTC
from datetime import datetime

import factory

from .models import CDCUser
from .models import Course
from .models import Location
from .models import Mentor
from .models import PartnerPasswordAccess
from .models import Session


class CourseFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: f"Test Course {n}")
    slug = factory.Sequence(lambda n: f"test-course-{n}")

    class Meta:
        model = Course


class LocationFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Test Location {n}")
    address = factory.Sequence(lambda n: f"{n} Street")
    city = "Chicago"
    state = "IL"
    zip = "60605"

    class Meta:
        model = Location


class CDCUserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"username_{n}")

    class Meta:
        model = CDCUser


class MentorFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(CDCUserFactory)
    is_active = True

    class Meta:
        model = Mentor


class SessionFactory(factory.django.DjangoModelFactory):
    course = factory.SubFactory(CourseFactory)
    location = factory.SubFactory(LocationFactory)
    start_date = datetime.now(UTC)
    password = ""
    instructor = factory.SubFactory(MentorFactory)

    class Meta:
        model = Session


class PartnerPasswordAccessFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(CDCUserFactory)
    session = factory.SubFactory(SessionFactory)

    class Meta:
        model = PartnerPasswordAccess
