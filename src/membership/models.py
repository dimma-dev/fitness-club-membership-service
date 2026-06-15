from django.db import models
from django.conf import settings

from plans.models import MembershipPlan


class Membership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        FROZEN = "FROZEN", "Frozen"
        EXPIRED = "EXPIRED", "Expired"
        PENDING = "PENDING", "Pending"

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    start_date = models.DateField()
    end_date = models.DateField()

    frozen_from = models.DateField(null=True, blank=True)
    frozen_to = models.DateField(null=True, blank=True)
    is_frozen_used = models.BooleanField(default=False)

    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    auto_renew = models.BooleanField(default=False)

    plan = models.OneToOneField(
        MembershipPlan,
    )

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_memberships",
    )
    plan = models.ForeignKey(
        MembershipPlan,
        on_delete=models.PROTECT(),
        related_name="plan_memberships",
    )

    def __str__(self) -> str:
        return (
            f"Membership #{self.pk}: {self.member} - "
            f"{self.plan.name} ({self.status})"
        )
