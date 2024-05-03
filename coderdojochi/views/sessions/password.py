from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from coderdojochi.models import Session, PartnerPasswordAccess

class PasswordSessionView(TemplateView):
    """
    This view handles the password protection for partner sessions. It ensures that only authenticated users can access the password page,
    retrieves the session object based on its ID, and processes the password form submission.
    """
    template_name = "sessions/password.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(PasswordSessionView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PasswordSessionView, self).get_context_data(**kwargs)
        session_id = kwargs.get('pk')
        session = get_object_or_404(Session, pk=session_id)
        context['session'] = session
        return context

    def post(self, request, *args, **kwargs):
        session_id = kwargs.get('pk')
        session = get_object_or_404(Session, pk=session_id)
        password_input = request.POST.get('password')

        context = self.get_context_data(**kwargs)

        if not password_input:
            context["error"] = "Must enter a password."
            return render(request, self.template_name, context)

        if session.password != password_input:
            context["error"] = "Invalid password."
            return render(request, self.template_name, context)

        # Get from user session or create an empty set
        authed_partner_sessions = request.session.get("authed_partner_sessions", [])

        # Add course session id to user session
        authed_partner_sessions.append(kwargs.get("pk"))

        # Remove duplicates
        authed_partner_sessions = list(set(authed_partner_sessions))

        # Store it.
        request.session["authed_partner_sessions"] = authed_partner_sessions

        if request.user.is_authenticated:
            PartnerPasswordAccess.objects.get_or_create(session=session, user=request.user)

        return redirect(session.get_absolute_url())
