from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from plans.models import MembershipPlan
from membership.models import Membership
from membership.serializers import MembershipCreateSerializer, FreezeSerializer

User = get_user_model()


class MembershipCreateSerializerTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email="member@example.com", password="password123")
        self.plan = MembershipPlan.objects.create(name="Standard", price=Decimal("50.00"), duration_days=30)

        factory = APIRequestFactory()
        request = factory.get('/')
        request.user = self.user
        self.serializer_context = {'request': request}

    def test_create_membership_success(self):
        data = {"plan": self.plan.id, "auto_renew": False}
        serializer = MembershipCreateSerializer(data=data, context=self.serializer_context)

        self.assertTrue(serializer.is_valid())

    def test_create_membership_fails_if_active_exists(self):

        Membership.objects.create(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            price_at_purchase=Decimal("50.00"),
            member=self.user,
            plan=self.plan,
            status=Membership.Status.ACTIVE
        )

        data = {"plan": self.plan.id, "auto_renew": False}
        serializer = MembershipCreateSerializer(data=data, context=self.serializer_context)

        self.assertFalse(serializer.is_valid())
        self.assertIn("You already have an active, frozen, or pending membership payment.", str(serializer.errors))


class FreezeSerializerTest(TestCase):

    def test_freeze_validation_success(self):
        tomorrow = date.today() + timedelta(days=1)
        two_weeks_later = tomorrow + timedelta(days=14)

        data = {"frozen_from": tomorrow, "frozen_to": two_weeks_later}
        serializer = FreezeSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_freeze_the_past_fails(self):
        yesterday = date.today() - timedelta(days=1)
        tomorrow = date.today() + timedelta(days=1)

        data = {"frozen_from": yesterday, "frozen_to": tomorrow}
        serializer = FreezeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("You can't freeze the past.", str(serializer.errors))

    def test_freeze_wrong_date_order_fails(self):
        tomorrow = date.today() + timedelta(days=1)

        data = {"frozen_from": tomorrow, "frozen_to": tomorrow}
        serializer = FreezeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("The 'to' date must be after the 'from' date.", str(serializer.errors))

    def test_freeze_period_exceeds_30_days_fails(self):
        tomorrow = date.today() + timedelta(days=1)
        too_late = tomorrow + timedelta(days=31)

        data = {"frozen_from": tomorrow, "frozen_to": too_late}
        serializer = FreezeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("Freeze period cannot exceed 30 days.", str(serializer.errors))
