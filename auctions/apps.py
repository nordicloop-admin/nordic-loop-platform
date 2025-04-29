from django.apps import AppConfig


class AuctionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auctions'
    verbose_name = 'Auctions'

    def ready(self):
        # Import signals to register them
        import auctions.signals
