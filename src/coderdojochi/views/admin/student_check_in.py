import operator

from collections import Counter

from coderdojochi.models import (
    Order,
    Session,
)
from coderdojochi.views.admin import AdminView

from django.contrib import messages
from django.db.models import (
    Case,
    Count,
    When,
)
from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.utils import timezone


class AdminStudentCheckInView(AdminView):
    template_name = 'session-check-in.html'

    def get_context_data(self, **kwargs):
        session_id = kwargs['session_id']
        session = get_object_or_404(Session, id=session_id)

        # Active Session
        active_session = True if timezone.now() < session.end_date else False

        # get the orders
        orders = Order.objects.select_related().filter(
            session_id=kwargs['session_id']
        ).annotate(
            num_attended=Count(
                Case(
                    When(
                        student__order__check_in__isnull=False,
                        then=1
                    )
                )
            ),
            num_missed=Count(
                Case(
                    When(
                        student__order__check_in__isnull=True,
                        then=1
                    )
                )
            )
        )

        if active_session:
            active_orders = orders.filter(
                is_active=True
            ).order_by(
                'student__first_name'
            )

        else:
            active_orders = orders.filter(
                is_active=True,
                check_in__isnull=False
            ).order_by(
                'student__first_name'
            )

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

        # Genders
        gender_count = sorted(
            dict(
                list(
                    Counter(
                        e.student.get_clean_gender() for e in active_orders
                    ).iteritems()
                )
            ).items(),
            key=operator.itemgetter(1)
        )

        # Ages
        ages = sorted(
            list(
                e.get_student_age() for e in active_orders
            )
        )

        age_count = sorted(
            dict(
                list(
                    Counter(ages).iteritems()
                )
            ).items(),
            key=operator.itemgetter(0)
        )

        # age_count = sorted(
        #     dict(
        #         list(
        #             Counter(ages).iteritems()
        #         )
        #     ).items(),
        #     key=operator.itemgetter(1),
        #     reverse=True
        # )

        # Average Age
        average_age = int(
            round(
                sum(ages) / float(len(ages))
            )
        ) if orders and ages else 0

        return {
            'session': session,
            'active_session': active_session,
            'active_orders': active_orders,
            'inactive_orders': inactive_orders,
            'no_show_orders': no_show_orders,
            'gender_count': gender_count,
            'age_count': age_count,
            'average_age': average_age,
            'checked_in_orders': checked_in_orders,
        }

    def post(self, request, *args, **kwargs):
        if 'order_id' in request.POST:
            order = get_object_or_404(
                Order,
                id=self.request.POST['order_id']
            )

            if order.check_in:
                order.check_in = None
            else:
                order.check_in = timezone.now()

            if (
                u'{} {}'.format(
                    order.guardian.user.first_name,
                    order.guardian.user.last_name
                ) !=
                request.POST['order_alternate_guardian']
            ):
                order.alternate_guardian = self.request.POST[
                    'order_alternate_guardian'
                ]

            order.save()
        else:
            messages.error(request, 'Invalid Order')

        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)
