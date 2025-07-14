from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'type', 'user', 'date', 'is_read')
    list_filter = ('type', 'is_read', 'date')
    search_fields = ('title', 'message')
    date_hierarchy = 'date'
