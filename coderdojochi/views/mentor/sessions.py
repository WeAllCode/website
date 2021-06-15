from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView

from ...models import Mentor, MentorOrder, Session


class SessionDetailView(DetailView):
    model = Session
    template_name = "mentor/session_detail.html"

    def get_context_data(self, **kwargs):
        session = self.object
        mentor = get_object_or_404(Mentor, user=self.request.user)

        session_orders = MentorOrder.objects.filter(
            session=session,
            is_active=True,
        )

        context = super().get_context_data(**kwargs)
        context["mentor_signed_up"] = session_orders.filter(mentor=mentor).exists()
        context["spots_remaining"] = session.mentor_capacity - session_orders.count()
        context["account"] = mentor

        context["active_mentors"] = Mentor.objects.filter(
            id__in=MentorOrder.objects.filter(
                session=self.object,
                is_active=True,
            ).values("mentor__id")
        )

        return context


class SessionCancelView(DetailView):
    model = Session
    template_name = "mentor/session_cancel.html"

    # redirect if order not found
    def get(self, request, *args, **kwargs):
        try: 
            self.object = self.get_object()
            session = self.object
            mentor = get_object_or_404(Mentor, user=self.request.user)
            mentor_order = MentorOrder.objects.get(
                session=session,
                mentor=mentor,
                is_active=True,
            )
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context) 
        except ObjectDoesNotExist:
            return redirect(session.get_absolute_url())


    def get_context_data(self, **kwargs):
        session = self.object
        mentor = get_object_or_404(Mentor, user=self.request.user)

        mentor_order = MentorOrder.objects.get(
            session=session,
            mentor=mentor,
            is_active=True,
        )

        context = super().get_context_data(**kwargs)
        # context["mentor_signed_up"] = session_orders.filter(mentor=mentor).exists()
        # context["spots_remaining"] = session.mentor_capacity - session_orders.count()
        # context["account"] = mentor

        # context["active_mentors"] = Mentor.objects.filter(
        #     id__in=MentorOrder.objects.filter(
        #         session=self.object,
        #         is_active=True,
        #     ).values("mentor__id")
        # )

        return context
