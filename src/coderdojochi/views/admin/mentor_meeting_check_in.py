from coderdojochi.models import MeetingOrder
from coderdojochi.views.admin import AdminView
from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.utils import timezone


class AdminMentorMeetingCheckInView(AdminView):
    template_name = 'meeting-check-in.html'

    def get_context_data(self, **kwargs):
        orders = MeetingOrder.objects.select_related().filter(
            meeting=kwargs['meeting_id']
        ).order_by(
            'mentor__user__first_name'
        )

        active_orders = orders.filter(
            is_active=True
        )

        inactive_orders = orders.filter(
            is_active=False
        )

        checked_in = orders.filter(
            is_active=True,
            check_in__isnull=False
        )

        return {
            'active_orders': active_orders,
            'inactive_orders': inactive_orders,
            'checked_in': checked_in,
        }

    def post(self, request, *args, **kwargs):
        if 'order_id' in request.POST:
            order = get_object_or_404(
                MeetingOrder,
                id=request.POST['order_id']
            )

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            order.save()
        else:
            messages.error(request, 'Invalid Order')

        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)
