from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from .models import CustomUser
from accounts.models import Company

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

    actions = ['approve_associated_companies', 'reject_associated_companies']

    @admin.action(description="Approve companies associated with selected users")
    def approve_associated_companies(self, request, queryset):
        from accounts.models import Company

        for user in queryset:
            # Find companies with matching email
            companies = Company.objects.filter(email=user.email, status='pending')

            for company in companies:
                try:
                    CustomUser.objects.approve_company(company.id, admin_user=request.user)
                    messages.success(request, f'Company "{company.official_name}" has been approved.')
                except ValueError as e:
                    messages.error(request, f'Error approving company for {user.email}: {str(e)}')

    @admin.action(description="Reject companies associated with selected users")
    def reject_associated_companies(self, request, queryset):
        from accounts.models import Company

        for user in queryset:
            # Find companies with matching email
            companies = Company.objects.filter(email=user.email, status='pending')

            for company in companies:
                try:
                    CustomUser.objects.reject_company(company.id)
                    messages.success(request, f'Company "{company.official_name}" has been rejected.')
                except ValueError as e:
                    messages.error(request, f'Error rejecting company for {user.email}: {str(e)}')
