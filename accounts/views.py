from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from coderdojochi.models import Guardian, MeetingOrder, Mentor, MentorOrder, Order, Student

from .forms import CDCModelForm, GuardianForm, MentorForm


class AccountHomeView(TemplateView):
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.role:
            if 'next' in request.GET:
                return redirect(
                    f"{reverse('welcome')}?next={request.GET['next']}"
                )
            else:
                messages.warning(
                    request,
                    'Tell us a little about yourself before going on to your dojo.'
                )
            return redirect('welcome')

        if request.user.role == 'mentor':
            return self.my_account_mentor(request)

        if request.user.role == 'guardian':
            return self.my_account_guardian(request)

    # TODO: upcoming classes needs to be all upcoming classes with a choice to RSVP in dojo page
    # TODO: upcoming meetings needs to be all upcoming meetings with a choice to RSVP in dojo page

    def my_account_mentor(self, request, template_name='account/home_mentor.html'):
        highlight = (
            request.GET['highlight'] if 'highlight' in request.GET else False
        )

        context = {
            'user': request.user,
            'highlight': highlight,
        }

        mentor = get_object_or_404(Mentor, user=request.user)

        orders = MentorOrder.objects.select_related().filter(
            is_active=True,
            mentor=mentor,
        )

        upcoming_sessions = orders.filter(
            is_active=True,
            session__end_date__gte=timezone.now()
        ).order_by('session__start_date')

        past_sessions = orders.filter(
            is_active=True,
            session__end_date__lte=timezone.now()
        ).order_by('session__start_date')

        meeting_orders = MeetingOrder.objects.select_related().filter(
            mentor=mentor
        )

        upcoming_meetings = meeting_orders.filter(
            is_active=True,
            meeting__is_public=True,
            meeting__end_date__gte=timezone.now()
        ).order_by('meeting__start_date')

        context['account_complete'] = False

        if (
            mentor.user.first_name and
            mentor.user.last_name and
            mentor.avatar and
            mentor.background_check and
            past_sessions.count() > 0
        ):
            context['account_complete'] = True

        if request.method == 'POST':
            form = MentorForm(
                request.POST,
                request.FILES,
                instance=mentor
            )

            user_form = CDCModelForm(
                request.POST,
                request.FILES,
                instance=mentor.user
            )

            if (
                form.is_valid() and
                user_form.is_valid()
            ):
                form.save()
                user_form.save()
                messages.success(
                    request,
                    'Profile information saved.'
                )

                return redirect('account_home')

            else:
                messages.error(
                    request,
                    'There was an error. Please try again.'
                )

        else:
            form = MentorForm(instance=mentor)
            user_form = CDCModelForm(instance=mentor.user)

        context['mentor'] = mentor
        context['upcoming_sessions'] = upcoming_sessions
        context['upcoming_meetings'] = upcoming_meetings
        context['past_sessions'] = past_sessions

        context['mentor'] = mentor
        context['form'] = form
        context['user_form'] = user_form

        return render(request, template_name, context)

    def my_account_guardian(self, request, template_name='account/home_guardian.html'):
        highlight = (
            request.GET['highlight'] if 'highlight' in request.GET else False
        )

        context = {
            'user': request.user,
            'highlight': highlight,
        }

        guardian = get_object_or_404(
            Guardian,
            user=request.user
        )

        students = Student.objects.filter(
            is_active=True,
            guardian=guardian,
        )

        student_orders = Order.objects.filter(
            student__in=students,
        )

        upcoming_orders = student_orders.filter(
            is_active=True,
            session__end_date__gte=timezone.now(),
        ).order_by('session__start_date')

        past_orders = student_orders.filter(
            is_active=True,
            session__end_date__lte=timezone.now(),
        ).order_by('session__start_date')

        if request.method == 'POST':
            form = GuardianForm(
                request.POST,
                instance=guardian
            )

            user_form = CDCModelForm(
                request.POST,
                instance=guardian.user
            )

            if form.is_valid() and user_form.is_valid():
                form.save()
                user_form.save()
                messages.success(
                    request,
                    'Profile information saved.'
                )

                return redirect('account_home')

            else:
                messages.error(
                    request,
                    'There was an error. Please try again.'
                )

        else:
            form = GuardianForm(instance=guardian)
            user_form = CDCModelForm(instance=guardian.user)

        context['students'] = students
        context['upcoming_orders'] = upcoming_orders
        context['past_orders'] = past_orders
        context['guardian'] = guardian
        context['form'] = form
        context['user_form'] = user_form

        return render(request, template_name, context)
