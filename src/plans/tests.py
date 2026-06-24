from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import MembershipPlan
from .serializers import MembershipPlanSerializer

User = get_user_model()


class MembershipPlanApiTests(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.regular_user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="password123", is_staff=True
        )

        self.plan_basic = MembershipPlan.objects.create(
            name="Basic Plan",
            code="basic-30",
            duration_days=30,
            price="29.99",
            tier=MembershipPlan.Tier.BASIC,
        )
        self.plan_premium = MembershipPlan.objects.create(
            name="Premium Plan",
            code="premium-90",
            duration_days=90,
            price="89.99",
            tier=MembershipPlan.Tier.PREMIUM,
        )

    def test_list_plans_unauthorized(self) -> None:
        url = reverse("membershipplan-list")
        res = self.client.get(url)

        plans = MembershipPlan.objects.all()
        serializer = MembershipPlanSerializer(plans, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_filter_plans_by_tier(self) -> None:
        url = reverse("membershipplan-list")
        res = self.client.get(url, {"tier": "BASIC"})

        plans = MembershipPlan.objects.filter(tier=MembershipPlan.Tier.BASIC)
        serializer = MembershipPlanSerializer(plans, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["results"], serializer.data)

    def test_plans_ordering_by_price(self) -> None:
        url = reverse("membershipplan-list")
        res = self.client.get(url)

        prices = [float(plan["price"]) for plan in res.data["results"]]
        self.assertEqual(prices, sorted(prices))

    def test_retrieve_plan_detail(self) -> None:
        url = reverse("membershipplan-detail", args=[self.plan_basic.id])
        res = self.client.get(url)

        serializer = MembershipPlanSerializer(self.plan_basic)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_plan_unauthorized(self) -> None:
        url = reverse("membershipplan-list")
        payload = {
            "name": "Standard Plan",
            "code": "standard-30",
            "duration_days": 30,
            "price": "49.99",
            "tier": "STANDARD",
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_plan_as_regular_user(self) -> None:
        self.client.force_authenticate(self.regular_user)
        url = reverse("membershipplan-list")
        payload = {
            "name": "Standard Plan",
            "code": "standard-30",
            "duration_days": 30,
            "price": "49.99",
            "tier": "STANDARD",
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_plan_as_admin(self) -> None:
        self.client.force_authenticate(self.admin_user)
        url = reverse("membershipplan-list")
        payload = {
            "name": "Standard Plan",
            "code": "standard-30",
            "duration_days": 30,
            "price": "49.99",
            "tier": "STANDARD",
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MembershipPlan.objects.filter(code="standard-30").exists())

    def test_create_plan_duplicate_code_fails(self) -> None:
        self.client.force_authenticate(self.admin_user)
        url = reverse("membershipplan-list")
        payload = {
            "name": "Another Basic Plan",
            "code": "basic-30",
            "duration_days": 30,
            "price": "29.99",
            "tier": "BASIC",
        }
        res = self.client.post(url, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", res.data)

    def test_create_plan_negative_price_fails(self) -> None:
        self.client.force_authenticate(self.admin_user)
        url = reverse("membershipplan-list")
        payload = {
            "name": "Negative Price Plan",
            "code": "negative-30",
            "duration_days": 30,
            "price": "-10.00",
            "tier": "BASIC",
        }
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", res.data)
        self.assertFalse(MembershipPlan.objects.filter(code="negative-30").exists())

    def test_full_update_plan_as_admin(self) -> None:
        self.client.force_authenticate(self.admin_user)
        url = reverse("membershipplan-detail", args=[self.plan_basic.id])
        payload = {
            "name": "Updated Basic Plan",
            "code": "basic-30-updated",
            "duration_days": 45,
            "price": "39.99",
            "tier": "BASIC",
        }
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.plan_basic.refresh_from_db()
        self.assertEqual(self.plan_basic.name, "Updated Basic Plan")
        self.assertEqual(self.plan_basic.duration_days, 45)
        self.assertEqual(str(self.plan_basic.price), "39.99")

    def test_delete_plan_as_admin(self) -> None:
        self.client.force_authenticate(self.admin_user)
        url = reverse("membershipplan-detail", args=[self.plan_basic.id])
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MembershipPlan.objects.filter(id=self.plan_basic.id).exists())
