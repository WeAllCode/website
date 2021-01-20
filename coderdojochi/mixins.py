from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


class RoleTemplateMixin(object):
    def get_template_names(self):
        if self.request.user.is_authenticated:
            if self.request.user.role == "mentor":
                template_name = f"mentor/{self.template_name}"
            elif self.request.user.role == "guardian":
                template_name = f"guardian/{self.template_name}"
        else:
            template_name = self.template_name

        return [template_name]


class RoleRedirectMixin(object):
    def dispatch(self, request, *args, **kwargs):
        session_obj = kwargs.get("session_obj")
        user = request.user

        if user.is_authenticated and session_obj and not user.role:
            messages.warning(request, "Please select one of the following options to continue.")

            next_url = f"{reverse('welcome')}?next={session_obj.get_absolute_url()}"

            if "enroll" in request.GET:
                next_url += "&enroll=True"

            return redirect(next_url)

        return super(RoleRedirectMixin, self).dispatch(request, *args, **kwargs)
