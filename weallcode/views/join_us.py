from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView

from ..forms import ContactForm
from .common import DefaultMetaTags


class JoinUsView(DefaultMetaTags, FormView):
    template_name = "weallcode/join_us.html"
    form_class = ContactForm
    url = reverse_lazy("weallcode-join-us")
    success_url = reverse_lazy("weallcode-join-us")

    title = f"Join Us | We All Code"

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_email()
        messages.success(
            self.request,
            "Thank you for contacting us! We will respond as soon as possible.",
        )

        return super().form_valid(form)
