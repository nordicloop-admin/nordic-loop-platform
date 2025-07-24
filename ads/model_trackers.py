from model_utils import FieldTracker
from django.db.models import signals
from .models import Ad

# Add a field tracker to the Ad model
Ad.add_to_class('tracker', FieldTracker(['is_active']))

# Connect the field tracker to the model
def connect_field_tracker():
    """
    Connect the field tracker to the Ad model after all apps are loaded.
    This ensures that the tracker is properly initialized.
    """
    # Ensure the tracker is properly initialized
    for instance in Ad.objects.all():
        if not hasattr(instance, '_tracker_initialized'):
            instance._tracker_initialized = True
