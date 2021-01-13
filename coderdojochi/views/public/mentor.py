from django.views.generic import DetailView, ListView

from ...models import Mentor


class MentorListView(ListView):
    model = Mentor

    def get_queryset(self):
        return (
            Mentor.objects.filter(
                user__is_active=True, is_active=True, is_public=True, background_check=True, avatar_approved=True,
            )
            .select_related("user")
            .order_by("user__date_joined")
        )


class MentorDetailView(DetailView):
    model = Mentor

    def get_queryset(self):
        return Mentor.objects.filter(
            user__is_active=True, is_active=True, is_public=True, background_check=True, avatar_approved=True,
        ).select_related("user")
