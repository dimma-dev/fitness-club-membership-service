from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from plans.models import MembershipPlan
from membership.models import Membership
from payments.models import Payment
from membership.tasks import (
    mark_expired_memberships,
    send_expiration_reminders,
    auto_renew_memberships,
)

User = get_user_model()


class MembershipCeleryTasksTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="client_tasks@example.com",
            password="password123",
            first_name="Павло",
            last_name="Переверзєв"
        )

        self.plan = MembershipPlan.objects.create(
            name="Super Plan",
            price=Decimal("120.00"),
            duration_days=30,
            code="task_plan_code"
        )

    @patch("membership.tasks.TelegramService.send_message")
    def test_mark_expired_memberships(self, mock_send_message):
        today = timezone.now().date()

        expired_membership = Membership.objects.create(
            start_date=today - timedelta(days=31),
            end_date=today - timedelta(days=1),
            price_at_purchase=Decimal("120.00"),
            member=self.user,
            plan=self.plan,
            status=Membership.Status.ACTIVE
        )

        active_membership = Membership.objects.create(
            start_date=today - timedelta(days=29),
            end_date=today + timedelta(days=1),
            price_at_purchase=Decimal("120.00"),
            member=self.user,
            plan=self.plan,
            status=Membership.Status.ACTIVE
        )

        result = mark_expired_memberships()

        self.assertEqual(result, "Marked 1 memberships as expired")

        expired_membership.refresh_from_db()
        active_membership.refresh_from_db()

        self.assertEqual(expired_membership.status, Membership.Status.EXPIRED)
        self.assertEqual(active_membership.status, Membership.Status.ACTIVE)

        mock_send_message.assert_called_once()

    @patch("membership.tasks.TelegramService.send_message")
    def test_send_expiration_reminders(self, mock_send_message):
        today = timezone.now().date()
        target_reminder_date = today + timedelta(days=7)

        Membership.objects.create(
            start_date=today - timedelta(days=23),
            end_date=target_reminder_date,
            price_at_purchase=Decimal("120.00"),
            member=self.user,
            plan=self.plan,
            status=Membership.Status.ACTIVE
        )

        result = send_expiration_reminders(days_before=7)

        self.assertEqual(result, "Sent 1 expiration reminders for 7 days before")
        mock_send_message.assert_called_once()

    @patch("membership.tasks.TelegramService.send_message")
    def test_auto_renew_memberships_success(self, mock_send_message):
        today = timezone.now().date()

        old_membership = Membership.objects.create(
            start_date=today - timedelta(days=31),
            end_date=today - timedelta(days=1),
            price_at_purchase=Decimal("120.00"),
            member=self.user,
            plan=self.plan,
            status=Membership.Status.EXPIRED,
            auto_renew=True
        )

        result = auto_renew_memberships()

        self.assertEqual(result, "Auto-renewed 1 memberships")

        old_membership.refresh_from_db()
        self.assertFalse(old_membership.auto_renew)

        new_membership = Membership.objects.filter(member=self.user, status=Membership.Status.ACTIVE).first()
        self.assertIsNotNone(new_membership)
        self.assertTrue(new_membership.auto_renew)
        self.assertEqual(new_membership.start_date, today)
        self.assertEqual(new_membership.end_date, today + timedelta(days=self.plan.duration_days))

        mock_send_message.assert_called_once()

    @patch("membership.tasks.TelegramService.send_message")
    def test_auto_renew_skipped_if_pending_payment_exists(self, mock_send_message):
        today = timezone.now().date()

        old_membership = Membership.objects.create(
            start_date=today - timedelta(days=31),
            end_date=today - timedelta(days=1),
            price_at_purchase=Decimal("120.00"),
            member=self.user,
            plan=self.plan,
            status=Membership.Status.EXPIRED,
            auto_renew=True
        )

        Payment.objects.create(
            membership=old_membership,
            money_to_pay=Decimal("120.00"),
            status=Payment.Status.PENDING,
            type=Payment.Type.MEMBERSHIP_PURCHASE
        )

        result = auto_renew_memberships()

        self.assertEqual(result, "Auto-renewed 0 memberships")
        mock_send_message.assert_not_called()
