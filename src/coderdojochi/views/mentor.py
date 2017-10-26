from django.http import Http404
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.shortcuts import redirect
from django.contrib import messages
from coderdojochi.models import Mentor


class MentorDetailView(DetailView):

    template_name = "mentor_detail.html"

    model = Mentor

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            return redirect('mentors_list')

        if not self.object.is_public:
            messages.error(self.request, 'Invalid mentor ID.')
            return redirect('mentors_list')

        context = self.get_context_data(object=self.object)

        return self.render_to_response(context)


class MentorListView(ListView):

    template_name = "mentor_list.html"

    model = Mentor

    def get_queryset(self):
        return Mentor.objects.filter(
            is_active=True,
            is_public=True,
            background_check=True,
            avatar_approved=True,
        ).order_by('user__date_joined')
