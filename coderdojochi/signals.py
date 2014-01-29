from registration.signals import user_registered
from django.shortcuts import get_object_or_404

from arb.models import Invite, Access


# def afterRegister(sender, user, request, **kwargs):

#     # do stuff with user


# user_registered.connect(afterRegister)
