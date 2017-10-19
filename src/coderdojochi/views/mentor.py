from django.http import Http404
from django.views.generic.detail import DetailView
from django.shortcuts import redirect
from django.contrib import messages

from coderdojochi.models import Mentor


class MentorDetailView(DetailView):
    template_name = "mentor-detail.html"

    model = Mentor


    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            return redirect('mentors')

        if not self.object.is_public:
            messages.error(self.request, 'Invalid mentor ID.')
            return redirect('mentors')

        context = self.get_context_data(object=self.object)


        return self.render_to_response(context)
