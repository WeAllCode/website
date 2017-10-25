from django.contrib import messages

from coderdojochi.views.admin import AdminView

from coderdojochi.models import (
	Session,
	MentorOrder
)

from django.shortcuts import (
	get_object_or_404,
	render
)
from django.utils import timezone


class AdminMentorCheckInView(AdminView):
	template_name = 'session-check-in-mentors.html'

	def get_context_data(self, **kwargs):
		session = get_object_or_404(Session, id=kwargs['session_id'])

		active_session = True if timezone.now() < session.end_date else False

		orders = MentorOrder.objects.select_related().filter(
			session_id=session.id
		)

		if active_session:
			active_orders = orders.filter(
				is_active=True
			).order_by('mentor__user__first_name')

		else:
			active_orders = orders.filter(
				is_active=True,
				check_in__isnull=False
			).order_by('mentor__user__first_name')

		inactive_orders = orders.filter(
			is_active=False
		).order_by('-updated_at')

		no_show_orders = orders.filter(
			is_active=True,
			check_in__isnull=True
		)

		checked_in_orders = orders.filter(
			is_active=True,
			check_in__isnull=False
		)

		return {
            'session': session,
            'active_session': active_session,
            'active_orders': active_orders,
            'inactive_orders': inactive_orders,
            'no_show_orders': no_show_orders,
            'checked_in_orders': checked_in_orders,
		}

	def post(self, request, *args, **kwargs):
		if 'order_id' in request.POST:
			order = get_object_or_404(
				MentorOrder,
				id=request.POST['order_id']
			)

			if order.check_in:
				order.check_in = None
			else:
				order.check_in = timezone.now()

			order.save()
		else:
			messages.error(
				request,
				'Invalid Order'
			)

		context = self.get_context_data(**kwargs)
		return render(request, self.template_name, context)
