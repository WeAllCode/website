from coderdojochi.forms import CDCModelForm, GuardianForm, MentorForm
from coderdojochi.models import (Guardian, MeetingOrder, Mentor, MentorOrder,
                                 Order, Student)
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from payments.models import Donation

User = get_user_model()


@method_decorator(login_required, name='dispatch')
class AccountHomeView(TemplateView):
    def dispatch(self, *args, **kwargs):
        if not self.request.user.role:
            if 'next' in self.request.GET:
                return redirect(
                    f"{reverse('welcome')}?next={self.request.GET['next']}"
                )
            else:
                messages.warning(
                    self.request,
                    'Tell us a little about yourself before going on account.'
                )
            return redirect('welcome')

        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['highlight'] = (
            self.request.GET['highlight'] if 'highlight' in self.request.GET else False
        )

        context['user'] = self.request.user

        if self.request.user.role == 'mentor':
            return {**context, **self.get_context_data_for_mentor()}

        if self.request.user.role == 'guardian':
            return {**context, **self.get_context_data_for_guardian()}

        return context

    def get_context_data_for_mentor(self):
        mentor = get_object_or_404(Mentor, user=self.request.user)

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

        account_complete = False

        if (
            mentor.user.first_name and
            mentor.user.last_name and
            mentor.avatar and
            mentor.background_check and
            past_sessions.count() > 0
        ):
            account_complete = True

        return {
            'mentor': mentor,
            'orders': orders,
            'upcoming_sessions': upcoming_sessions,
            'past_sessions': upcoming_sessions,
            'meeting_orders': meeting_orders,
            'upcoming_meetings': upcoming_meetings,
            'account_complete': account_complete
        }

    def get_context_data_for_guardian(self):
        guardian = get_object_or_404(
            Guardian,
            user=self.request.user
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

        return {
            'guardian': guardian,
            'students': students,
            'student_orders': student_orders,
            'upcoming_orders': upcoming_orders,
            'past_orders': past_orders,
        }

    def get(self, *args, **kwargs):
        if self.request.user.role == 'mentor':
            return self.get_for_mentor(**kwargs)

        if self.request.user.role == 'guardian':
            return self.get_for_guardian(**kwargs)

    def get_for_mentor(self, **kwargs):
        context = self.get_context_data(**kwargs)

        context['form'] = MentorForm(instance=context['mentor'])
        context['user_form'] = CDCModelForm(instance=context['mentor'].user)

        return render(self.request, 'account/home_mentor.html', context)

    def get_for_guardian(self, **kwargs):
        context = self.get_context_data(**kwargs)

        context['form'] = GuardianForm(instance=context['guardian'])
        context['user_form'] = CDCModelForm(instance=context['guardian'].user)

        return render(self.request, 'account/home_guardian.html', context)

    def post(self, *args, **kwargs):
        if self.request.user.role == 'mentor':
            return self.post_for_mentor(**kwargs)

        if self.request.user.role == 'guardian':
            return self.post_for_guardian(**kwargs)

    def post_for_mentor(self, **kwargs):
        context = self.get_context_data(**kwargs)

        mentor = context['mentor']

        form = MentorForm(
            self.request.POST,
            self.request.FILES,
            instance=mentor
        )

        user_form = CDCModelForm(
            self.request.POST,
            self.request.FILES,
            instance=mentor.user
        )

        if (
            form.is_valid() and
            user_form.is_valid()
        ):
            form.save()
            user_form.save()
            messages.success(
                self.request,
                'Profile information saved.'
            )

            return redirect('account-home')

        else:
            messages.error(
                self.request,
                'There was an error. Please try again.'
            )

        context['form'] = form
        context['user_form'] = user_form

        return render(self.request, 'account/home_mentor.html', context)

    def post_for_guardian(self, **kwargs):
        context = self.get_context_data(**kwargs)

        guardian = context['guardian']

        form = GuardianForm(
            self.request.POST,
            instance=guardian
        )

        user_form = CDCModelForm(
            self.request.POST,
            instance=guardian.user
        )

        if form.is_valid() and user_form.is_valid():
            form.save()
            user_form.save()
            messages.success(
                self.request,
                'Profile information saved.'
            )

            return redirect('account-home')

        else:
            messages.error(
                self.request,
                'There was an error. Please try again.'
            )

        context['form'] = form
        context['user_form'] = user_form

        return render(self.request, 'account/home_guardian.html', context)


@method_decorator(login_required, name='dispatch')
class PaymentsView(ListView):
    model = Donation
    template_name = "account/account-payments.html"
    # queryset = Donation.objects.filter(customer='ACME Publishing')

    def get_queryset(self):
        return Donation.objects.filter(customer=self.request.user).order_by('-created_at')
