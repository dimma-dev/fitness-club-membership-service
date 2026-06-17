from django.db import models


class Payment(models.Model):

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"

    class Type(models.TextChoices):
        MEMBERSHIP_PURCHASE = (
            "MEMBERSHIP_PURCHASE",
            "Membership Purchase"
        )
        UPGRADE_FEE = (
            "UPGRADE_FEE",
            "Upgrade Fee"
        )

    membership = models.ForeignKey(
        "membership.Membership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    type = models.CharField(
        max_length=30,
        choices=Type.choices
    )

    money_to_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    session_url = models.URLField(
        max_length=500,
        null=True,
        blank=True
    )

    session_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"Payment #{self.pk} "
            f"[{self.type}] - {self.status}"
        )
