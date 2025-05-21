from django.db import models
from ads.models import Ad
from users.models import User

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="users")
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name="bids")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    volume = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) 
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.amount} on {self.ad}"


# Create your models here.
