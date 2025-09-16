from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'type', 'user_email', 'date', 'is_read', 'message_preview')
    list_filter = ('type', 'is_read', 'date')
    search_fields = ('title', 'message', 'user__email', 'user__username')
    date_hierarchy = 'date'
    readonly_fields = ('date',)
    list_editable = ('is_read',)
    ordering = ['-date']
    
    fieldsets = (
        ('Notification Information', {
            'fields': ('user', 'title', 'message', 'type')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamps', {
            'fields': ('date',),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def message_preview(self, obj):
        """Show a preview of the message"""
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message Preview'
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = 'Mark selected notifications as unread'
