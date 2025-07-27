from django.apps import AppConfig


class AdsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ads'
    
    def ready(self):
        # Import and connect model trackers
        import ads.model_trackers
        ads.model_trackers.connect_field_tracker()

        # Import signals
        import category_subscriptions.signals
        import ads.subscription_signals
