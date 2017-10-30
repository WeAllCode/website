from django.views.generic.list import ListView
from django.utils import timezone
from collections import Counter
import operator
from django.db.models import (
    Case,
    Count,
    IntegerField,
    When,
)
from coderdojochi.models import (
    Order,
    Session,
)

class AdminClassesListView(ListView):
    # pass
    model = Session

    template_name = 'admin_classes_list.html'

    # def get_queryset(self):
    #     return Session.objects.filter().order_by('-start_date')

    def get_context_data(self, **kwargs):
        context = super(AdminClassesListView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()

        context['object_list'] = Session.objects.select_related().annotate(
            num_orders=Count(
                'order'
            ),

            num_attended=Count(
                Case(
                    When(
                        order__check_in__isnull=False,
                        then=1
                    )
                )
            ),

            is_future=Case(
                When(
                    end_date__gte=timezone.now(),
                    then=1
                ),
                default=0,
                output_field=IntegerField(),
            )
        ).order_by(
            '-start_date'
        )

        orders = Order.objects.select_related()

        total_past_orders = orders.filter(is_active=True)
        context['total_past_orders_count'] = total_past_orders.count()
        total_checked_in_orders = orders.filter(
            is_active=True,
            check_in__isnull=False
        )
        context['total_checked_in_orders_count'] = total_checked_in_orders.count()

        context['upcoming_sessions'] = orders.filter(
            is_active=True,
            session__end_date__gte=timezone.now()
        ).order_by('session__start_date')

        # Genders
        context['gender_count'] = list(
            Counter(
                e.student.get_clean_gender() for e in total_checked_in_orders
            ).iteritems()
        )
        context['gender_count'] = sorted(
            dict(context['gender_count']).items(),
            key=operator.itemgetter(1)
        )

        # Ages
        ages = sorted(
            list(
               e.student.get_age() for e in total_checked_in_orders
            )
        )
        context['age_count'] = sorted(
           dict(
              list(
                Counter(ages).iteritems()
              )
            ).items(),
           key=operator.itemgetter(0)
        )

        # Average Age
        context['average_age'] = int(
           round(
             sum(ages) / float(len(ages))
           )
        )

        return context


    #     return render(
#         request,
#         template_name,
#         {


#             # 'upcoming_sessions': upcoming_sessions,
#             # 'upcoming_sessions_count': upcoming_sessions_count,
#         }
#     )

# @login_required
# def cdc_admin(request, template_name="admin.html"):
#     if not request.user.is_staff:
#         messages.error(
#             request,
#             'You do not have permission to access this page.'
#         )
#         return redirect('sessions')

#     sessions = Session.objects.select_related().annotate(
#         num_orders=Count(
#             'order'
#         ),

#         num_attended=Count(
#             Case(
#                 When(
#                     order__check_in__isnull=False,
#                     then=1
#                 )
#             )
#         ),

#         is_future=Case(
#             When(
#                 end_date__gte=timezone.now(),
#                 then=1
#             ),
#             default=0,
#             output_field=IntegerField(),
#         )
#     ).order_by(
#         '-start_date'
#     )



#     meetings = Meeting.objects.select_related().annotate(
#         num_orders=Count(
#             'meetingorder'
#         ),

#         num_attended=Count(
#             Case(
#                 When(
#                     meetingorder__check_in__isnull=False,
#                     then=1
#                 )
#             )
#         ),

#         is_future=Case(
#             When(
#                 end_date__gte=timezone.now(),
#                 then=1
#             ),
#             default=0,
#             output_field=IntegerField(),
#         )

#     ).order_by(
#         '-start_date'
#     )





#     orders = Order.objects.select_related()

#     total_past_orders = orders.filter(is_active=True)
#     total_past_orders_count = total_past_orders.count()
#     total_checked_in_orders = orders.filter(
#         is_active=True,
#         check_in__isnull=False
#     )
#     total_checked_in_orders_count = total_checked_in_orders.count()

#     # Genders
#     gender_count = list(
#         Counter(
#             e.student.get_clean_gender() for e in total_checked_in_orders
#         ).iteritems()
#     )
#     gender_count = sorted(
#         dict(gender_count).items(),
#         key=operator.itemgetter(1)
#     )

#     # Ages
#     ages = sorted(
#         list(
#             e.student.get_age() for e in total_checked_in_orders
#         )
#     )
#     age_count = sorted(
#         dict(
#             list(
#                 Counter(ages).iteritems()
#             )
#         ).items(),
#         key=operator.itemgetter(0)
#     )

#     # Average Age
#     average_age = int(
#         round(
#             sum(ages) / float(len(ages))
#         )
#     )

#     return render(
#         request,
#         template_name,
#         {
#             'age_count': age_count,
#             'average_age': average_age,
#             'gender_count': gender_count,
#             'meetings': meetings,
#             # 'past_meetings_count': past_meetings_count,
#             # 'past_sessions': past_sessions,
#             # 'past_sessions_count': past_sessions_count,
#             'sessions': sessions,
#             'total_checked_in_orders_count': total_checked_in_orders_count,
#             'total_past_orders_count': total_past_orders_count,
#             # 'upcoming_meetings': upcoming_meetings,
#             # 'upcoming_meetings_count': upcoming_meetings_count,
#             # 'upcoming_sessions': upcoming_sessions,
#             # 'upcoming_sessions_count': upcoming_sessions_count,
#         }
#     )
