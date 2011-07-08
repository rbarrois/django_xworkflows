def setup(app, *args):
    from django.conf import settings

    if not settings.configured:
        settings.configure()
