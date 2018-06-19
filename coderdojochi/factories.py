from datetime import datetime

import factory
from pytz import utc

from .models import CDCUser, Course, Location, Mentor, PartnerPasswordAccess, Session


class CourseFactory(factory.DjangoModelFactory):
    title = factory.Sequence(lambda n: f"Test Course {n}")
    slug = factory.Sequence(lambda n: f"test-course-{n}")

    class Meta:
        model = Course


class LocationFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Test Location {n}")
    address = factory.Sequence(lambda n: f"{n} Street")
    city = 'Chicago'
    state = 'IL'
    zip = '60605'

    class Meta:
        model = Location


class CDCUserFactory(factory.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"username_{n}")

    class Meta:
        model = CDCUser


class MentorFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(CDCUserFactory)
    active = True

    class Meta:
        model = Mentor


class SessionFactory(factory.DjangoModelFactory):
    course = factory.SubFactory(CourseFactory)
    location = factory.SubFactory(LocationFactory)
    start_date = datetime.now(utc)
    end_date = datetime.now(utc)
    mentor_start_date = datetime.now(utc)
    mentor_end_date = datetime.now(utc)
    password = ''
    teacher = factory.SubFactory(MentorFactory)

    class Meta:
        model = Session


class PartnerPasswordAccessFactory(factory.DjangoModelFactory):
    user = factory.SubFactory(CDCUserFactory)
    session = factory.SubFactory(SessionFactory)

    class Meta:
        model = PartnerPasswordAccess
