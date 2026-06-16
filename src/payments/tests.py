from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from plans.models import MembershipPlan
from membership.models import Membership
from payments.models import Payment
from datetime import date, timedelta

User = get_user_model()


class PaymentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
        )
        self.plan = MembershipPlan.objects.create(
            name="Basic",
            code="basic",
            duration_days=30,
            price=50.00,
            tier="BASIC",
        )
        self.membership = Membership.objects.create(
            member=self.user,
            plan=self.plan,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            price_at_purchase=50.00,
        )

    def test_payment_created(self):
        payment = Payment.objects.create(
            membership=self.membership,
            type=Payment.Type.MEMBERSHIP_PURCHASE,
            money_to_pay=50.00,
            session_url="https://stripe.com/test",
            session_id="cs_test_123",
        )
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.type, Payment.Type.MEMBERSHIP_PURCHASE)

    def test_payment_str(self):
        payment = Payment.objects.create(
            membership=self.membership,
            type=Payment.Type.MEMBERSHIP_PURCHASE,
            money_to_pay=50.00,
            session_url="https://stripe.com/test",
            session_id="cs_test_123",
        )
        self.assertIn("MEMBERSHIP_PURCHASE", str(payment))


class PaymentSuccessViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com",
            password="testpass123",
        )
        self.plan = MembershipPlan.objects.create(
            name="Basic",
            code="basic",
            duration_days=30,
            price=50.00,
            tier="BASIC",
        )
        self.membership = Membership.objects.create(
            member=self.user,
            plan=self.plan,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            price_at_purchase=50.00,
        )
        self.payment = Payment.objects.create(
            membership=self.membership,
            type=Payment.Type.MEMBERSHIP_PURCHASE,
            money_to_pay=50.00,
            session_url="https://stripe.com/test",
            session_id="cs_test_123",
        )

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_success_marks_payment_paid(self, mock_retrieve):
        mock_session = MagicMock()
        mock_session.payment_status = "paid"
        mock_retrieve.return_value = mock_session

        response = self.client.get(
            reverse("payment-success") + "?session_id=cs_test_123"
        )
        self.assertEqual(response.status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_success_not_paid(self, mock_retrieve):
        mock_session = MagicMock()
        mock_session.payment_status = "unpaid"
        mock_retrieve.return_value = mock_session

        response = self.client.get(
            reverse("payment-success") + "?session_id=cs_test_123"
        )
        self.assertEqual(response.status_code, 400)

    def test_success_no_session_id(self):
        response = self.client.get(reverse("payment-success"))
        self.assertEqual(response.status_code, 400)

    def test_cancel_view(self):
        response = self.client.get(reverse("payment-cancel"))
        self.assertEqual(response.status_code, 200)
