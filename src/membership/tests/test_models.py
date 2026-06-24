from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.db.models.deletion import ProtectedError
from datetime import date
from decimal import Decimal

from plans.models import MembershipPlan
from membership.models import Membership

User = get_user_model()


class MembershipModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123"
        )

        self.plan = MembershipPlan.objects.create(
            name="Premium",
            price=Decimal("100.00"),
            duration_days=30
        )

    def test_membership_creation_and_defaults(self):
        membership = Membership.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            price_at_purchase=Decimal("90.00"),
            member=self.user,
            plan=self.plan
        )

        self.assertEqual(membership.status, Membership.Status.PENDING)
        self.assertFalse(membership.is_frozen_used)
        self.assertFalse(membership.auto_renew)

        self.assertIsNone(membership.frozen_from)
        self.assertIsNone(membership.frozen_to)

    def test_membership_str_representation(self):
        membership = Membership.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            price_at_purchase=Decimal("100.00"),
            member=self.user,
            plan=self.plan,
            status=Membership.Status.ACTIVE
        )
        expected_str = f"Membership #{membership.pk}: {self.user} - Premium (ACTIVE)"
        self.assertEqual(str(membership), expected_str)

    def test_on_delete_cascade_for_member(self):
        Membership.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            price_at_purchase=Decimal("100.00"),
            member=self.user,
            plan=self.plan
        )

        self.assertEqual(Membership.objects.count(), 1)

        self.user.delete()

        self.assertEqual(Membership.objects.count(), 0)

    def test_on_delete_protect_for_plan(self):
        Membership.objects.create(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            price_at_purchase=Decimal("100.00"),
            member=self.user,
            plan=self.plan
        )

        with self.assertRaises(ProtectedError):
            self.plan.delete()

    def test_required_fields(self):
        with self.assertRaises(IntegrityError):
            Membership.objects.create(
                member=self.user,
                plan=self.plan
            )
