from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from ...models import Mentor, MentorOrder, Session


class SessionDetailView(DetailView):
    model = Session
    template_name = "mentor/session-detail.html"

    def get_context_data(self, **kwargs):
        session = self.object
        mentor = get_object_or_404(Mentor, user=self.request.user)

        session_orders = MentorOrder.objects.filter(
            session=session,
            mentor=mentor,
            is_active=True,
        )

        context = super().get_context_data(**kwargs)
        context["mentor_signed_up"] = session_orders.exists()
        context["spots_remaining"] = session.get_mentor_capacity() - session_orders.count()
        context["account"] = mentor

        return context
