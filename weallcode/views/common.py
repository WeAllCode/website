from django.contrib.auth import get_user_model
from meta.views import MetadataMixin

User = get_user_model()


class DefaultMetaTags(MetadataMixin):
    title = None
    description = (
        "We All Code is volunteer run nonprofit organization that teaches web,"
        " game, and app development to youth ages 7 to 17 free of charge."
    )
    image = "weallcode/images/photos/real-coding-skills.jpg"
    twitter_card = "summary_large_image"
    twitter_creator = "@weallcode"
    twitter_site = "@weallcode"
