def user_display(user):
    """How allauth names a user on screen and in emails (ACCOUNT_USER_DISPLAY).

    allauth defaults to the username, which here is an opaque generated value.
    Show the full name, falling back to the email address.
    """
    return user.get_full_name() or user.email or user.username
