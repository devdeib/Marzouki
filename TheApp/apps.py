from django.apps import AppConfig


class TheappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "TheApp"

    def ready(self):
        # Wire up signal handlers (cache invalidation, etc.).
        from . import signals  # noqa: F401
