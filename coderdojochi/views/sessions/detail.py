from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from coderdojochi.models import Session

class SessionDetailView(DetailView):
    """
    This view handles the display of details for a specific session.
    It retrieves the session object based on its primary key (pk) and
    renders it using the 'session_detail.html' template.
    """
    model = Session
    template_name = "session_detail.html"

    def get_context_data(self, **kwargs):
        """
        Extends the context data with custom data if needed.
        """
        context = super().get_context_data(**kwargs)
        return context
