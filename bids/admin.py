from django.contrib import admin
from .models import Bid

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "ad", "amount", "timestamp")
    list_filter = ("timestamp", "ad", "user")
    ordering = ("-timestamp",)