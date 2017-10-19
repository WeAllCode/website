from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from coderdojochi.forms import (
    GuardianForm,
    MentorForm,
    StudentForm,
)
from coderdojochi.models import (
    Guardian,
    Meeting,
    Mentor,
    Session,
)


class WelcomeView(TemplateView):
    template_name = "welcome.html"

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        next_url = request.GET.get('next')
        kwargs['next_url'] = next_url
        # Check for redirect condition on mentor, otherwise pass as kwarg
        if (
            getattr(request.user, 'role', False) == 'mentor'
            and request.method == 'GET'
        ):
            mentor = get_object_or_404(Mentor, user=request.user)
            if mentor.user.first_name:
                return redirect(next_url if next_url else 'dojo')
            kwargs['mentor'] = mentor
        return super(WelcomeView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(WelcomeView, self).get_context_data(**kwargs)
        user = self.request.user
        mentor = kwargs.get('mentor')
        account = False
        role = getattr(user, 'role', False)

        context['role'] = role
        context['next_url'] = kwargs['next_url']

        if mentor:
            account = mentor
            context['form'] = MentorForm(instance=account)
        if role == 'guardian':
            guardian = get_object_or_404(Guardian, user=user)
            account = guardian
            if not account.phone or not account.zip:
                context['form'] = GuardianForm(instance=account)
            else:
                context['add_student'] = True
                context['form'] = StudentForm(
                    initial={'guardian': guardian.pk}
                )

            if account.user.first_name and account.get_students():
                context['students'] = account.get_students().count()

        context['account'] = account

        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        role = getattr(user, 'role', False)
        next_url = kwargs['next_url']

        if role:
            if role == 'mentor':
                account = get_object_or_404(Mentor, user=user)
                return self.update_account(request, account, next_url)
            account = get_object_or_404(Guardian, user=user)

            if not account.phone or not account.zip:
                return self.update_account(request, account, next_url)

            return self.add_student(request, account, next_url)
        else:
            return self.create_new_user(request, user, next_url)

    def update_account(self, request, account, next_url):
        if isinstance(account, Mentor):
            form = MentorForm(request.POST, instance=account)
            role = 'mentor'
        else:
            form = GuardianForm(request.POST, instance=account)
            role = 'guardian'
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile information saved.')
            if next_url:
                if 'enroll' in request.GET:
                    next_url = u'{}?enroll=True'.format(next_url)
            else:
                next_url = 'dojo' if isinstance(account, Mentor) else 'welcome'
            return redirect(next_url)

        return render(request, self.template_name, {
            'form': form,
            'role': role,
            'account': account,
            'next_url': next_url
        })

    def add_student(self, request, account, next_url):
        form = StudentForm(request.POST)
        if form.is_valid():
            new_student = form.save(commit=False)
            new_student.guardian = account
            new_student.save()
            messages.success(request, 'Student Registered.')
            if next_url:
                if 'enroll' in request.GET:
                    next_url = u'{}?enroll=True&student={}'.format(
                        next_url, new_student.id
                    )
            else:
                next_url = 'welcome'
            return redirect(next_url)

        return render(request, self.template_name, {
            'form': form,
            'role': 'guardian',
            'account': account,
            'next_url': next_url,
            'add_student': True
        })

    def create_new_user(self, request, user, next_url):
        if request.POST.get('role') == 'mentor':
            role = 'mentor'
            account, created = Mentor.objects.get_or_create(user=user)
        else:
            role = 'guardian'
            account, created = Guardian.objects.get_or_create(user=user)

        account.user.first_name = user.first_name
        account.user.last_name = user.last_name
        account.save()

        user.role = role
        user.save()

        merge_vars = {
            'user': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name
        }

        next_url = u'?next={}'.format(next_url) if next_url else None

        if role == 'mentor':
            # check for next upcoming meeting
            next_meeting = Meeting.objects.filter(
                is_active=True,
                is_public=True
            ).order_by('start_date').first()

            if next_meeting:
                merge_vars[
                    'next_intro_meeting_url'
                ] = next_meeting.get_absolute_url()

                merge_vars[
                    'next_intro_meeting_ics_url'
                ] = next_meeting.get_ics_url()
            if not next_url:
                next_url = reverse('dojo')
        else:
            # check for next upcoming class
            next_class = Session.objects.filter(
                is_active=True
            ).order_by('start_date').first()

            if next_class:
                merge_vars[
                    'next_class_url'
                ] = next_class.get_absolute_url()

                merge_vars[
                    'next_class_ics_url'
                ] = next_class.get_ics_url()
            if not next_url:
                next_url = reverse('welcome')

        email(
            subject='Welcome!',
            template_name='welcome-{}'.format(role),
            context=merge_vars,
            recipients=[user.email],
            preheader='Your adventure awaits!',
        )

        return redirect(next_url)
