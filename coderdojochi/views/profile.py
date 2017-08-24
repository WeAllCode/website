from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


class DojoMentorView(TemplateView):
    template_name = 'mentor/dojo.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(DojoMentorView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DojoMentorView, self).get_context_data(**kwargs)
        context['highlight'] = request.GET.get('highlight', False)
        mentor = get_object_or_404(Mentor, user=request.user)
        context['mentor'] = mentor

        orders = MentorOrder.objects.select_related().filter(
            is_active=True,
            mentor=context['mentor'],
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
        return context

    def post(self, request, *args, **kwargs):
        mentor = get_object_or_404(Mentor, user=request.user)

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

            return redirect('dojo')

        else:
            messages.error(
                request,
                'There was an error. Please try again.'
            )


@login_required
def dojo_mentor(request, template_name='mentor/dojo.html'):

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

            return redirect('dojo')

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
