from datetime import date, timedelta
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from membership.filters import MembershipFilter
from membership.models import Membership
from membership.serializers import (
    FreezeSerializer,
    MembershipCreateSerializer,
    MembershipReadSerializer,
)
from payments.models import Payment
from plans.models import MembershipPlan

@extend_schema(tags=["Memberships"])
class MembershipViewSet(viewsets.ModelViewSet):
    """
        API endpoint for managing fitness club memberships.
        Access is restricted to authorized clients only.
        """
    queryset = Membership.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = MembershipFilter

    def get_queryset(self):
        user = self.request.user
        base_queryset = Membership.objects.select_related("plan", "member")
        if user.is_staff:
            return base_queryset
        return base_queryset.filter(member=user)

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return MembershipReadSerializer
        return MembershipCreateSerializer

    def perform_create(self, serializer):
        user = self.request.user
        plan = serializer.validated_data["plan"]
        start_date = date.today()
        end_date = start_date + timedelta(days=plan.duration_days)

        with transaction.atomic():
            membership = serializer.save(
                member=user,
                start_date=start_date,
                end_date=end_date,
                price_at_purchase=plan.price,
                status=Membership.Status.PENDING,
            )

            Payment.objects.create(
                user=user,
                status=Payment.Status.PENDING,
                type=Payment.Type.MEMBERSHIP_PURCHASE,
                membership_id=membership.id,
                money_to_pay=membership.price_at_purchase
            )

    @action(detail=True, methods=["post"])
    def freeze(self, request, pk=None):
        membership = self.get_object()

        # Проверки состояния абонемента в базе данных оставляем здесь
        if membership.status != Membership.Status.ACTIVE:
            return Response(
                {"error": "Only an active subscription can be frozen."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if membership.is_frozen_used:
            return Response(
                {"error": "This subscription has already been frozen."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        frozen_from = serializer.validated_data["frozen_from"]
        frozen_to = serializer.validated_data["frozen_to"]
        freeze_days = (frozen_to - frozen_from).days

        with transaction.atomic():
            membership.status = Membership.Status.FROZEN
            membership.frozen_from = frozen_from
            membership.frozen_to = frozen_to
            membership.is_frozen_used = True
            membership.end_date += timedelta(days=freeze_days)
            membership.save()

        return Response(MembershipReadSerializer(membership).data)

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        membership = self.get_object()

        if membership.status != Membership.Status.FROZEN:
            return Response(
                {"error": "The subscription is not frozen."},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = date.today()

        if membership.frozen_to and today < membership.frozen_to:
            unused_freeze_days = (membership.frozen_to - today).days

            membership.end_date -= timedelta(days=unused_freeze_days)

        with transaction.atomic():
            membership.status = Membership.Status.ACTIVE
            membership.frozen_from = None
            membership.frozen_to = None
            membership.save()

        return Response(MembershipReadSerializer(membership).data)

    @action(detail=True, methods=["post"])
    def upgrade(self, request, pk=None):
        membership = self.get_object()
        new_plan_id = request.query_params.get("plan_id")

        try:
            new_plan = MembershipPlan.objects.get(id=new_plan_id)
        except MembershipPlan.DoesNotExist:
            return Response(
                {"error": "Plan not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if new_plan.price <= membership.plan.price:
            return Response(
                {"error": "Upgrade is only possible to a more expensive plan."},
                status=status.HTTP_400_BAD_REQUEST
            )

        today = date.today()
        remaining_days = max(0, (membership.end_date - today).days)

        credit = (membership.plan.price / membership.plan.duration_days) * remaining_days
        new_full_price = (new_plan.price / new_plan.duration_days) * remaining_days

        upgrade_fee = round(max(0, new_full_price - credit), 2)

        with transaction.atomic():
            payment = Payment.objects.create(
                user=request.user,
                status=Payment.Status.PENDING,
                type=Payment.Type.UPGRADE_FEE,
                membership_id=membership.id,
                money_to_pay=upgrade_fee
            )

            return Response({
                "message": "Upgrade payment created. Once paid, your plan will be updated.",
                "payment_id": payment.id,
                "amount_to_pay": payment.money_to_pay,
                "new_plan_name": new_plan.name
            }, status=status.HTTP_201_CREATED)
