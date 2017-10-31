from coderdojochi.models import Meeting
from django.db.models import Case, Count, IntegerField, When
from django.utils import timezone
from django.views.generic.list import ListView

class AdminMeetingsListView(ListView):

    model = Meeting

    template_name = 'admin_meetings_list.html'

    def get_context_data(self, **kwargs):
        context = super(AdminMeetingsListView, self).get_context_data(**kwargs)
        context['object_list'] = Meeting.objects.select_related().annotate(
            num_orders=Count(
                'meetingorder'
            ),

            num_attended=Count(
                Case(
                    When(
                        meetingorder__check_in__isnull=False,
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

        return context
