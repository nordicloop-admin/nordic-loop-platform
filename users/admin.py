from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "name",
        "company",
        "can_place_ads",
        "can_place_bids",
        "is_staff",
        "is_active",
        "is_superuser",
        "last_login",
        "date_joined",
        "role",
    ]
    list_filter = ["is_staff", "is_superuser", "is_active", "company"]
    search_fields = ["username", "email", "first_name", "last_name", "name"]
    ordering = ["-date_joined"]
    readonly_fields = ["last_login", "date_joined"]
