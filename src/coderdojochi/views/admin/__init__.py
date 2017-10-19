from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import TemplateView


@method_decorator(never_cache, name='dispatch')
@method_decorator(login_required, name='dispatch')
class AdminView(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(
                request, 'You do not have permission to access this page.'
            )

            return redirect('sessions')

        return super(TemplateView, self).dispatch(request, *args, **kwargs)
