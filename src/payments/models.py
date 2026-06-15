from django.db import models


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING"
        PAID = "PAID"

    class Type(models.TextChoices):
        MEMBERSHIP_PURCHASE = "MEMBERSHIP_PURCHASE"
        UPGRADE_FEE = "UPGRADE_FEE"

    membership = models.ForeignKey(
        "membership.Membership", on_delete=models.CASCADE, related_name="payments"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    type = models.CharField(max_length=30, choices=Type.choices)
    session_url = models.URLField()
    session_id = models.CharField(max_length=255)
    money_to_pay = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"Payment #{self.pk} for membership {self.membership_id} ({self.status})"
