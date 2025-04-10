from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'name', 'subscription_status', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'subscription_status', 'date_joined')
    search_fields = ('email', 'name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('email', 'name', 'password')
        }),
        ('Subscription', {
            'fields': ('subscription_status',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')
