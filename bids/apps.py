from django.apps import AppConfig


class BidsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bids'

    def ready(self):  # pragma: no cover
        try:
            import bids.signals  # noqa: F401
        except Exception:
            pass

