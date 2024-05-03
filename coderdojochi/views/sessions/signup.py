from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from coderdojochi.models import Session, Order, Guardian, Student

class SessionSignUpView(TemplateView):
    """
    This view handles the sign-up process for a session. It ensures that only authenticated users can access the sign-up page,
    retrieves the session object based on its ID, and processes the sign-up form submission.
    """
    template_name = "sessions/signup.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(SessionSignUpView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SessionSignUpView, self).get_context_data(**kwargs)
        session_id = kwargs.get('pk')
        session = get_object_or_404(Session, pk=session_id)
        context['session'] = session
        return context

    def post(self, request, *args, **kwargs):
        session_id = kwargs.get('pk')
        session = get_object_or_404(Session, pk=session_id)
        guardian = get_object_or_404(Guardian, user=request.user)
        student_id = request.POST.get('student_id')
        student = get_object_or_404(Student, pk=student_id)

        # Check if the student is already signed up for the session
        if Order.objects.filter(session=session, student=student).exists():
            # Redirect with error message
            return redirect(session.get_absolute_url())

        # Create a new order for the session sign-up
        Order.objects.create(
            session=session,
            student=student,
            guardian=guardian
        )

        # Redirect to the session detail page
        return redirect(session.get_absolute_url())
