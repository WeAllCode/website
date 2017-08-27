import factory
from datetime import datetime
from pytz import utc

from models import Session
from models import Course
from models import Location
from models import Mentor
from models import CDCUser
from models import PartnerPasswordAccess


class CourseFactory(factory.DjangoModelFactory):
    title = factory.Sequence(lambda n: 'Test Course {}'.format(n))
    slug = factory.Sequence(lambda n: 'test-course-{}'.format(n))

    class Meta:
        model = Course


class LocationFactory(factory.DjangoModelFactory):
    name = factory.Sequence(lambda n: 'Test Location {}'.format(n))
    address = factory.Sequence(lambda n: '{} Street'.format(n))
    city = 'Chicago'
    state = 'IL'
    zip = '60605'

    class Meta:
        model = Location


class CDCUserFactory(factory.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'username_{}'.format(n))

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
