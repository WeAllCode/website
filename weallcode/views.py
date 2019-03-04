from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "weallcode/home.html"


class OurStoryView(TemplateView):
    template_name = "weallcode/our_story.html"


class LearnView(TemplateView):
    template_name = "weallcode/learn.html"


class TeamView(TemplateView):
    template_name = "weallcode/team.html"


class GetInvolvedView(TemplateView):
    template_name = "weallcode/get_involved.html"
