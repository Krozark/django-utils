from django.contrib.auth import get_user_model


def create_user(username="john", **kwargs):
    return get_user_model().objects.create_user(username=username, **kwargs)
