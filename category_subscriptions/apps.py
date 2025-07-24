from django.apps import AppConfig


class CategorySubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'category_subscriptions'
    
    def ready(self):
        import category_subscriptions.signals
