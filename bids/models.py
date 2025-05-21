from django.db import models
from ads.models import Ad
from users.models import User

class Bid(models.Model):
    STATUS_CHOICE =[
        ("Outbid", "Outbid"),
        ("Highest_bid", "Highest_bid")

    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="users")
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_Highest_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    status = models.CharField(max_length=20, choices=STATUS_CHOICE, null=True, default="Highest_bid")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.amount} on {self.ad}"



