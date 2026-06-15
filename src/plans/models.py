from django.db import models


class MembershipPlan(models.Model):

    class Tier(models.TextChoices):
        BASIC = "basic", "Basic"
        PRO = "pro", "Pro"
        PREMIUM = "premium", "Premium"

    name = models.CharField(max_length=100)
    code = models.SlugField(unique=True)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tier = models.CharField(max_length=10, choices=Tier.choices)

    def __str__(self):
        return self.name
