# -*- coding: utf-8 -*-

import arrow
import calendar
import logging
import operator

from collections import Counter
from datetime import date, timedelta
from icalendar import Calendar, Event, vText
from paypal.standard.forms import PayPalPaymentsForm

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import (
    Case,
    Count,
    IntegerField,
    When,
)
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.functional import cached_property
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, TemplateView

from coderdojochi.util import email
from coderdojochi.models import (
    Donation,
    Equipment,
    EquipmentType,
    Guardian,
    Meeting,
    MeetingOrder,
    Mentor,
    MentorOrder,
    Order,
    PartnerPasswordAccess,
    Session,
    Student,
)
from coderdojochi.forms import (
    CDCModelForm,
    ContactForm,
    GuardianForm,
    MentorForm,
    StudentForm,
    DonationForm
)
from coderdojochi.mixins import RoleRedirectMixin
from coderdojochi.views.general import IcsView

logger = logging.getLogger("mechanize")

# this will assign User to our custom CDCUser
User = get_user_model()


def session_confirm_mentor(request, session_obj, order):
    email(
        subject='Mentoring confirmation for {} class'.format(
            arrow.get(
                session_obj.mentor_start_date
            ).to('local').format('MMMM D'),
        ),
        template_name='class-confirm-mentor',
        context={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'class_code': session_obj.course.code,
            'class_title': session_obj.course.title,
            'class_description': session_obj.course.description,
            'class_start_date': arrow.get(
                session_obj.mentor_start_date
            ).to('local').format('dddd, MMMM D, YYYY'),
            'class_start_time': arrow.get(
                session_obj.mentor_start_date
            ).to('local').format('h:mma'),
            'class_end_date': arrow.get(
                session_obj.mentor_end_date
            ).to('local').format('dddd, MMMM D, YYYY'),
            'class_end_time': arrow.get(
                session_obj.mentor_end_date
            ).to('local').format('h:mma'),
            'class_location_name': session_obj.location.name,
            'class_location_address': session_obj.location.address,
            'class_location_address2': (
                session_obj.location.address2
            ),
            'class_location_city': session_obj.location.city,
            'class_location_state': session_obj.location.state,
            'class_location_zip': session_obj.location.zip,
            'class_additional_info': session_obj.additional_info,
            'class_url': session_obj.get_absolute_url(),
            'class_ics_url': session_obj.get_ics_url(),
            'microdata_start_date': arrow.get(
                session_obj.mentor_start_date
            ).to('local').isoformat(),
            'microdata_end_date': arrow.get(
                session_obj.mentor_end_date
            ).to('local').isoformat(),
            'order': order,
        },
        recipients=[request.user.email],
        preheader='It\'s time to use your powers for good.',
    )


def session_confirm_guardian(request, session_obj, order, student):
    email(
        subject='Upcoming class confirmation for {} {}'.format(
            student.first_name,
            student.last_name,
        ),
        template_name='class-confirm-guardian',
        context={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'student_first_name': student.first_name,
            'student_last_name': student.last_name,
            'class_code': session_obj.course.code,
            'class_title': session_obj.course.title,
            'class_description': session_obj.course.description,
            'class_start_date': arrow.get(
                session_obj.start_date
            ).to('local').format('dddd, MMMM D, YYYY'),
            'class_start_time': arrow.get(
                session_obj.start_date
            ).to('local').format('h:mma'),
            'class_end_date': arrow.get(
                session_obj.end_date
            ).to('local').format('dddd, MMMM D, YYYY'),
            'class_end_time': arrow.get(
                session_obj.end_date
            ).to('local').format('h:mma'),
            'class_location_name': session_obj.location.name,
            'class_location_address': session_obj.location.address,
            'class_location_address2': (
                session_obj.location.address2
            ),
            'class_location_city': session_obj.location.city,
            'class_location_state': session_obj.location.state,
            'class_location_zip': session_obj.location.zip,
            'class_additional_info': session_obj.additional_info,
            'class_url': session_obj.get_absolute_url(),
            'class_ics_url': session_obj.get_ics_url(),
            'microdata_start_date': arrow.get(
                session_obj.start_date
            ).to('local').isoformat(),
            'microdata_end_date': arrow.get(
                session_obj.end_date
            ).to('local').isoformat(),
            'order': order,
        },
        recipients=[request.user.email],
        preheader='Magical wizards have generated this '
                  'confirmation. All thanks to the mystical '
                  'power of coding.',
    )


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])

    return date(year, month, day)


class SessionsView(TemplateView):
    template_name = "sessions.html"
    
    def get_context_data(self, **kwargs):
        context = super(SessionsView, self).get_context_data(**kwargs)
        now = timezone.now()
        year = int(kwargs.get('year')) if kwargs.get('year') else now.year
        month = int(kwargs.get('month')) if kwargs.get('month') else now.month 
        calendar_date = date(day=1, month=month, year=year)
        
        context['prev_date'] = add_months(calendar_date, -1)
        context['next_date'] = add_months(calendar_date, 1)
        context['calendar_date'] = calendar_date
        
        all_sessions = Session.objects.filter(
            is_active=True,
            end_date__gte=now
        ).order_by('start_date')
        
        if (
            not self.request.user.is_authenticated() or
            not self.request.user.role == 'mentor'
        ):
            all_sessions = all_sessions.filter(is_public=True)
            
        context['all_sessions'] = all_sessions 
        context['sessions'] = all_sessions.filter(
            start_date__year=year,
            start_date__month=month
        ).order_by('start_date')
        
        return context


class SessionDetailView(RoleRedirectMixin, TemplateView):
    template_name = "session-detail.html"

    def dispatch(self, request, *args, **kwargs):
        session_obj = get_object_or_404(Session, id=kwargs['session_id'])
        if request.method == 'GET':
            # Replaces session_detail_short
            if all([k not in kwargs for k in ['year', 'month', 'day', 'slug']]):
                return redirect(session_obj.get_absolute_url())
            if session_obj.password:
                if not self.validate_partner_session_access(self.request, kwargs['session_id']):
                    return redirect(reverse('session_password', kwargs=kwargs))
            if request.user.is_authenticated() and request.user.role:
                if 'enroll' in request.GET or 'enroll' in kwargs:
                    return self.enroll_redirect(request, session_obj)
        kwargs['session_obj'] = session_obj
        return super(SessionDetailView, self).dispatch(request, *args, **kwargs)

    def enroll_redirect(self, request, session_obj):
        if request.user.role == 'mentor':
            return redirect(u'{}/sign-up/'.format(session_obj.get_absolute_url()))
        guardian = get_object_or_404(Guardian, user=request.user)
        students = guardian.get_students()
        if students and 'student' in request.GET:
            return redirect(u'{}/sign-up/{}'.format(
                session_obj.get_absolute_url(),
                request.GET['student']
            ))
        return redirect(u'{}?next={}&enroll=True'.format(
            reverse('welcome'),
            session_obj.get_absolute_url()
        ))

    def validate_partner_session_access(self, request, session_id):
        authed_sessions = request.session.get('authed_partner_sessions')

        if authed_sessions and session_id in authed_sessions:
            if request.user.is_authenticated():
                PartnerPasswordAccess.objects.get_or_create(
                    session_id=session_id,
                    user=request.user
                )
            return True

        if request.user.is_authenticated():
            try:
                PartnerPasswordAccess.objects.get(
                    session_id=session_id,
                    user_id=request.user.id
                )
            except PartnerPasswordAccess.DoesNotExist:
                return False
            else:
                return True

        else:
            return False

    def get_context_data(self, **kwargs):
        context = super(SessionDetailView, self).get_context_data(**kwargs)
        session_obj = kwargs['session_obj']
        context['session'] = session_obj

        upcoming_classes = Session.objects.filter(
            is_active=True,
            end_date__gte=timezone.now()
        ).order_by('start_date')
        context['upcoming_classes'] = upcoming_classes

        if self.request.user.is_authenticated():
            if self.request.user.role == 'mentor':
                account = get_object_or_404(Mentor, user=self.request.user)
                session_orders = MentorOrder.objects.filter(
                    session=session_obj,
                    is_active=True,
                )
                context['mentor_signed_up'] = session_orders.filter(
                    mentor=account
                ).exists()

                context['spots_remaining'] = (
                    session_obj.get_mentor_capacity() - session_orders.count()
                )
            else:
                account = get_object_or_404(Guardian, user=self.request.user)
                context['students'] = account.get_students()
                context['spots_remaining'] = (
                    session_obj.capacity - 
                    session_obj.get_current_students().count()
                )
            context['account'] = account
        else:
            context['upcoming_classes'] = upcoming_classes.filter(is_public=True)
            context['spots_remaining'] = (
                session_obj.capacity - 
                session_obj.get_current_students().count()
            )

        return context

    def post(self, request, *args, **kwargs):
        session_obj = kwargs['session_obj']
        if 'waitlist' not in request.POST:
            messages.error(request, 'Invalid request, please try again.')
            return redirect(session_obj.get_absolute_url())

        if request.POST['waitlist'] == 'student':
            account = Student.objects.get(id=request.POST['account'])
            waitlist_attr = 'waitlist_students'
        else:
            account = Guardian.objects.get(id=request.POST['account'])
            waitlist_attr = 'waitlist_guardians'

        if request.POST['remove'] == 'true':
            getattr(session_obj, waitlist_attr).remove(account)
            session_obj.save()
            messages.success(
                request,
                'You have been removed from the waitlist. '
                'Thanks for letting us know.'
            )
        else:
            getattr(session_obj, waitlist_attr).add(account)
            session_obj.save()
            messages.success(
                request,
                'Added to waitlist successfully.'
            )
        return redirect(session_obj.get_absolute_url())


class SessionSignUpView(RoleRedirectMixin, TemplateView):
    template_name = "session-sign-up.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        session_obj = get_object_or_404(Session, id=kwargs['session_id'])
        kwargs['session_obj'] = session_obj
        if request.user.role == 'mentor':
            session_orders = MentorOrder.objects.filter(
                session=session_obj,
                is_active=True
            )
            kwargs['mentor'] = get_object_or_404(Mentor, user=request.user)
            kwargs['user_signed_up'] = session_orders.filter(
                mentor=kwargs['mentor']
            ).exists()
        elif request.user.role == 'guardian':
            kwargs['guardian'] = get_object_or_404(Guardian, user=request.user)
            kwargs['student'] = get_object_or_404(Student, id=kwargs['student_id'])
            kwargs['user_signed_up'] = kwargs['student'].is_registered_for_session(session_obj)

        access_dict = self.check_access(request, *args, **kwargs)
        if access_dict.get('message'):
            if access_dict.get('redirect') == 'dojo':
                messages.warning(access_dict['message'])
            else:
                messages.error(access_dict['message'])
            return redirect(access_dict['redirect'])

        return super(SessionSignUpView, self).dispatch(request, *args, **kwargs)

    def check_access(self, request, *args, **kwargs):
        access_dict = {}
        # Returns a message and redirect url if not working as dict
        if kwargs.get('mentor'):
            if not kwargs['mentor'].background_check:
                access_dict = {
                    'message': u'You cannot sign up for a class until you '
                               u'<a href="{}" target="_blank">'
                               u'fill out the background search form'
                               u'</a>.'.format(
                                    'https://app.verifiedvolunteers.com/promoorder/'
                                    '6a34f727-3728-4f1a-b80b-7eb3265a3b93'
                               ),
                    'redirect': 'dojo'
                }
        if kwargs.get('student'):
            limits = self.student_limitations(
                kwargs['student'], kwargs['session_obj'], kwargs['user_signed_up']
            )
            if limits:
                access_dict = {
                    'message': limits, 
                    'redirect': kwargs['session_obj'].get_absolute_url()
                }
        return access_dict

    def student_limitations(self, student, session_obj, user_signed_up):
        if not student.is_within_gender_limitation(
                session_obj.gender_limitation
            ):
            return ('Sorry, this class is limited to {}s '
                    'this time around.'.format(
                        session_obj.gender_limitation
                    ))
        if not student.is_within_age_range(
                session_obj.min_age_limitation,
                session_obj.max_age_limitation
            ):
            return ('Sorry, this class is limited to students between ages '
                    '{} and {}.'.format(
                        session_obj.min_age_limitation,
                        session_obj.max_age_limitation
                    ))
        if not user_signed_up:
            if session_obj.capacity <= session_obj.get_current_students().count():
                return ('Sorry this class has sold out. '
                        'Please sign up for the wait list '
                        'and/or check back later.')
        return False
        
    def get_context_data(self, **kwargs):
        context = super(SessionSignUpView, self).get_context_data(**kwargs)
        context['session'] = kwargs['session_obj']
        context['user_signed_up'] = kwargs.get('user_signed_up')
        context['student'] = kwargs.get('student')
        return context

    def post(self, request, *args, **kwargs):
        session_obj = kwargs['session_obj']
        user_signed_up = kwargs['user_signed_up']
        mentor = kwargs.get('mentor')
        guardian = kwargs.get('guardian')
        student = kwargs.get('student')
        
        if user_signed_up:
            if mentor:
                order = get_object_or_404(
                    MentorOrder, 
                    mentor=mentor,
                    session=session_obj
                )
            elif student:
                order = get_object_or_404(
                    Order,
                    student=student,
                    session=session_obj,
                    is_active=True,
                )
            order.is_active = False
            order.save()
            
            messages.success(request, 'Thanks for letting us know!')
        else:
            if not settings.DEBUG:
                ip = (
                    request.META['HTTP_X_FORWARDED_FOR'] or
                    request.META['REMOTE_ADDR']
                )

            else:
                ip = request.META['REMOTE_ADDR']
                
            if mentor:
                order, created = MentorOrder.objects.get_or_create(
                    mentor=mentor,
                    session=session_obj,
                )
            else:
                order, created = Order.objects.get_or_create(
                    guardian=guardian,
                    student=student,
                    session=session_obj,
                )
            order.ip = ip 
            order.is_active = True
            order.save()
            
            messages.success(request, 'Success! See you there!')
            
            if mentor:
                session_confirm_mentor(request, session_obj, order)
            else:
                session_confirm_guardian(request, session_obj, order, student)
                
        return redirect(session_obj.get_absolute_url())


class PasswordSessionView(TemplateView):
    template_name = 'session-partner-password.html'

    def get_context_data(self, **kwargs):
        context = super(PasswordSessionView, self).get_context_data(**kwargs)

        session_id = kwargs.get('session_id')
        session_obj = get_object_or_404(Session, id=session_id)

        context['partner_message'] = session_obj.partner_message

        return context

    def post(self, request, *args, **kwargs):
        session_id = kwargs.get('session_id')
        session_obj = get_object_or_404(Session, id=session_id)
        password_input = request.POST.get('password')

        context = self.get_context_data(**kwargs)

        if not password_input:
            context['error'] = 'Must enter a password.'
            return render(request, self.template_name, context)

        if session_obj.password != password_input:
            context['error'] = 'Invalid password.'
            return render(request, self.template_name, context)

        # Get from user session or create an empty set
        authed_partner_sessions = request.session.get(
            'authed_partner_sessions'
        ) or set()

        # Add course session id to user session
        authed_partner_sessions.update({session_id})

        # Store it.
        request.session['authed_partner_sessions'] = authed_partner_sessions

        if request.user.is_authenticated():
            PartnerPasswordAccess.objects.get_or_create(
                session=session_obj,
                user=request.user
            )

        return HttpResponseRedirect(
            reverse(
                'session_detail',
                kwargs=kwargs
            )
        )


class SessionIcsView(IcsView):
    event_type = 'class'
    event_kwarg = 'session_id'
    event_class = Session
    
    def get_summary(self, request, event_obj):
        return u'CoderDojoChi: {} - {}'.format(
            event_obj.course.code,
            event_obj.course.title
        )
        
    def get_dtstart(self, request, event_obj):
        start_date = arrow.get(event_obj.start_date).format('YYYYMMDDTHHmmss')
        dtstart = '{}Z'.format(start_date)
        if request.user.is_authenticated() and request.user.role == 'mentor':
            dtstart = '{}Z'.format(arrow.get(
                event_obj.mentor_start_date
            ).format('YYYYMMDDTHHmmss'))
        return dtstart
        
    def get_dtend(self, request, event_obj):
        end_date = arrow.get(event_obj.end_date).format('YYYYMMDDTHHmmss')
        dtend = '{}Z'.format(end_date)
        if request.user.is_authenticated() and request.user.role == 'mentor':
            dtend = '{}Z'.format(arrow.get(
                event_obj.mentor_end_date
            ).format('YYYYMMDDTHHmmss'))
        return dtend
        
    def get_description(self, event_obj):
        return strip_tags(event_obj.course.description)
