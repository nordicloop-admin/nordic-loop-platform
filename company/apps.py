from django.apps import AppConfig


class CompanyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'company'

    def ready(self):  # pragma: no cover - import side-effect
        # Import signals so that they are registered when Django starts
        try:
            import company.signals  # noqa: F401
        except Exception:  # Defensive: don't break startup if import fails
            # Optional: integrate logging here if desired
            pass
