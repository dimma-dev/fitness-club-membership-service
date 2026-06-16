from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from plans.models import MembershipPlan
from membership.models import Membership

User = get_user_model()


class MembershipActionsTestCase(APITestCase):

    def setUp(self):
        # Создаем тестового пользователя без поля username (используется email)
        self.user = User.objects.create_user(email="gym_member@example.com", password="password123")
        self.client.force_authenticate(user=self.user)

        # Создаем базовый план с обязательными полями duration_days и уникальным code
        self.base_plan = MembershipPlan.objects.create(
            name="Base",
            price=Decimal("100.00"),
            duration_days=100,
            code="base_code"
        )

        # Создаем дорогой план для проверки апгрейда с другим уникальным кодом
        self.gold_plan = MembershipPlan.objects.create(
            name="Gold",
            price=Decimal("250.00"),
            duration_days=100,
            code="gold_code"
        )

        # Создаем базовый активный абонемент для пользователя
        self.membership = Membership.objects.create(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=100),
            price_at_purchase=Decimal("100.00"),
            member=self.user,
            plan=self.base_plan,
            status=Membership.Status.ACTIVE
        )

    @patch("membership.views.notify_membership_frozen.delay")
    def test_freeze_membership_success(self, mock_celery):
        """Успешная заморозка абонемента со сдвигом даты окончания"""
        url = f"/api/memberships/{self.membership.pk}/freeze/"

        frozen_from = date.today() + timedelta(days=1)
        frozen_to = date.today() + timedelta(days=11)  # Заморозка на 10 дней

        data = {
            "frozen_from": str(frozen_from),
            "frozen_to": str(frozen_to)
        }

        old_end_date = self.membership.end_date
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Обновляем данные из БД
        self.membership.refresh_from_db()

        self.assertEqual(self.membership.status, Membership.Status.FROZEN)
        self.assertTrue(self.membership.is_frozen_used)
        self.assertEqual(self.membership.end_date, old_end_date + timedelta(days=10))
        mock_celery.assert_called_once_with(self.membership.id)

    def test_freeze_membership_already_used_fails(self):
        """Нельзя заморозить абонемент, если заморозка уже была использована ранее"""
        self.membership.is_frozen_used = True
        self.membership.save()

        url = f"/api/memberships/{self.membership.pk}/freeze/"
        data = {
            "frozen_from": str(date.today() + timedelta(days=1)),
            "frozen_to": str(date.today() + timedelta(days=5))
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "This subscription has already been frozen.")

    def test_resume_membership_recalculates_end_date(self):
        """Досрочная разморозка должна вернуть неиспользованные дни обратно"""
        self.membership.status = Membership.Status.FROZEN
        self.membership.frozen_from = date.today() - timedelta(days=2)
        self.membership.frozen_to = date.today() + timedelta(days=10)
        original_end_date = self.membership.end_date
        self.membership.save()

        url = f"/api/memberships/{self.membership.pk}/resume/"
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.membership.refresh_from_db()

        self.assertEqual(self.membership.status, Membership.Status.ACTIVE)
        self.assertIsNone(self.membership.frozen_from)
        self.assertIsNone(self.membership.frozen_to)
        self.assertEqual(self.membership.end_date, original_end_date - timedelta(days=10))

    @patch("membership.views.create_stripe_session")
    def test_upgrade_membership_success(self, mock_stripe):
        """Проверка расчета стоимости апгрейда и создания сессии Stripe"""
        mock_payment = MagicMock()
        mock_payment.id = 42
        mock_payment.money_to_pay = Decimal("75.00")
        mock_stripe.return_value = mock_payment

        url = f"/api/memberships/{self.membership.pk}/upgrade/?plan_id={self.gold_plan.id}"

        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["new_plan_name"], "Gold")
        self.assertEqual(response.data["payment_id"], 42)
        mock_stripe.assert_called_once()

    def test_upgrade_to_cheaper_plan_fails(self):
        """Нельзя проапгрейдиться на план, который дешевле или равен текущему"""
        cheap_plan = MembershipPlan.objects.create(
            name="Cheap",
            price=Decimal("50.00"),
            duration_days=100,
            code="cheap_code"
        )

        url = f"/api/memberships/{self.membership.pk}/upgrade/?plan_id={cheap_plan.id}"
        response = self.client.post(url, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Upgrade is only possible to a more expensive plan.")