from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from plans.models import MembershipPlan
from membership.models import Membership
from payments.models import Payment
from payments.serializers import PaymentSerializer
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

    def test_payment_type_choices(self):
        payment = Payment.objects.create(
            membership=self.membership,
            type=Payment.Type.UPGRADE_FEE,
            money_to_pay=25.00,
            session_id="cs_test_456",
        )
        self.assertEqual(payment.type, Payment.Type.UPGRADE_FEE)

    def test_payment_ordering(self):
        payment1 = Payment.objects.create(
            membership=self.membership,
            type=Payment.Type.MEMBERSHIP_PURCHASE,
            money_to_pay=50.00,
            session_id="cs_test_1",
        )
        payment2 = Payment.objects.create(
            membership=self.membership,
            type=Payment.Type.MEMBERSHIP_PURCHASE,
            money_to_pay=50.00,
            session_id="cs_test_2",
        )
        payments = list(Payment.objects.all())
        self.assertEqual(payments[0].id, payment2.id)
        self.assertEqual(payments[1].id, payment1.id)


class PaymentSerializerTest(TestCase):
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

    def test_serializer_valid_data(self):
        data = {
            "membership": self.membership.id,
            "type": Payment.Type.MEMBERSHIP_PURCHASE,
            "money_to_pay": 50.00,
        }
        serializer = PaymentSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_serializer_invalid_negative_amount(self):
        data = {
            "membership": self.membership.id,
            "type": Payment.Type.MEMBERSHIP_PURCHASE,
            "money_to_pay": -10.00,
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("money_to_pay", serializer.errors)

    def test_serializer_invalid_zero_amount(self):
        data = {
            "membership": self.membership.id,
            "type": Payment.Type.MEMBERSHIP_PURCHASE,
            "money_to_pay": 0,
        }
        serializer = PaymentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("money_to_pay", serializer.errors)

    def test_serializer_read_only_fields(self):
        payment = Payment.objects.create(
            membership=self.membership,
            type=Payment.Type.MEMBERSHIP_PURCHASE,
            money_to_pay=50.00,
            session_url="https://stripe.com/test",
            session_id="cs_test_123",
        )
        serializer = PaymentSerializer(payment)
        self.assertEqual(serializer.data["status"], Payment.Status.PENDING)
        self.assertEqual(serializer.data["session_id"], "cs_test_123")


class CreateCheckoutSessionViewTest(TestCase):
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

    def test_create_checkout_session_requires_auth(self):
        data = {
            "membership_id": self.membership.id,
            "payment_type": Payment.Type.MEMBERSHIP_PURCHASE,
        }
        response = self.client.post(
            reverse("create-checkout-session"),
            data=data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("payments.views.StripeService.create_checkout_session")
    def test_create_checkout_session_authenticated(self, mock_service):
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/test"
        mock_service.return_value = mock_session

        self.client.force_authenticate(user=self.user)
        data = {
            "membership_id": self.membership.id,
            "payment_type": Payment.Type.MEMBERSHIP_PURCHASE,
        }
        response = self.client.post(
            reverse("create-checkout-session"),
            data=data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("checkout_url", response.data)

    @patch("payments.views.StripeService.create_checkout_session")
    def test_create_checkout_session_with_exception(self, mock_service):
        mock_service.side_effect = Exception("Stripe error")

        self.client.force_authenticate(user=self.user)
        data = {
            "membership_id": self.membership.id,
            "payment_type": Payment.Type.MEMBERSHIP_PURCHASE,
        }
        response = self.client.post(
            reverse("create-checkout-session"),
            data=data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)

    @patch("payments.views.StripeService.create_checkout_session")
    def test_create_checkout_session_invalid_membership(self, mock_service):
        self.client.force_authenticate(user=self.user)
        data = {
            "membership_id": 99999,
            "payment_type": Payment.Type.MEMBERSHIP_PURCHASE,
        }
        response = self.client.post(
            reverse("create-checkout-session"),
            data=data,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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

    def test_success_with_valid_session_id(self):
        response = self.client.get(
            reverse("payment-success") + "?session_id=cs_test_123"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["payment_id"], self.payment.id)
        self.assertIn("status", response.data)

    def test_success_with_invalid_session_id(self):
        response = self.client.get(
            reverse("payment-success") + "?session_id=cs_invalid_999"
        )
        self.assertEqual(response.status_code, 404)

    def test_success_no_session_id(self):
        response = self.client.get(reverse("payment-success"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)


class PaymentCancelViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_cancel_view(self):
        response = self.client.get(reverse("payment-cancel"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.data)


class StripeWebhookViewTest(TestCase):
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

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_webhook_invalid_signature(self, mock_construct):
        import stripe as stripe_module
        mock_construct.side_effect = stripe_module.error.SignatureVerificationError(
            "sig_header", "payload"
        )

        response = self.client.post(
            reverse("stripe-webhook"),
            data={},
            HTTP_STRIPE_SIGNATURE="invalid_sig"
        )
        self.assertEqual(response.status_code, 400)

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_webhook_non_payment_event(self, mock_construct):
        mock_event = {
            "type": "customer.created",
            "data": {"object": {}}
        }
        mock_construct.return_value = mock_event

        response = self.client.post(
            reverse("stripe-webhook"),
            data={},
            HTTP_STRIPE_SIGNATURE="valid_sig"
        )
        self.assertEqual(response.status_code, 200)

    @patch("payments.views.stripe.Webhook.construct_event")
    @patch("payments.views.notify_payment_success.delay")
    def test_webhook_successful_payment(self, mock_notify, mock_construct):
        mock_session = MagicMock()
        mock_session.metadata = {"payment_id": str(self.payment.id)}
        
        mock_event = {
            "type": "checkout.session.completed",
            "data": {"object": mock_session}
        }
        mock_construct.return_value = mock_event

        response = self.client.post(
            reverse("stripe-webhook"),
            data={},
            HTTP_STRIPE_SIGNATURE="valid_sig"
        )
        self.assertEqual(response.status_code, 200)
        
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_webhook_missing_payment_id(self, mock_construct):
        mock_session = MagicMock()
        mock_session.metadata = {}
        
        mock_event = {
            "type": "checkout.session.completed",
            "data": {"object": mock_session}
        }
        mock_construct.return_value = mock_event

        response = self.client.post(
            reverse("stripe-webhook"),
            data={},
            HTTP_STRIPE_SIGNATURE="valid_sig"
        )
        self.assertEqual(response.status_code, 200)

    @patch("payments.views.stripe.Webhook.construct_event")
    def test_webhook_invalid_payment_id_format(self, mock_construct):
        mock_session = MagicMock()
        mock_session.metadata = {"payment_id": "invalid_string"}
        
        mock_event = {
            "type": "checkout.session.completed",
            "data": {"object": mock_session}
        }
        mock_construct.return_value = mock_event

        response = self.client.post(
            reverse("stripe-webhook"),
            data={},
            HTTP_STRIPE_SIGNATURE="valid_sig"
        )
        self.assertEqual(response.status_code, 400)
