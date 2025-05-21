from django.contrib import admin
from .models import Bid

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "ad", "amount","current_Highest_amount", "timestamp")
    list_filter = ("timestamp", "ad", "user", "current_Highest_amount")
    ordering = ("-timestamp",)