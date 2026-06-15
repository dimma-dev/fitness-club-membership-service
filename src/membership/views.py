from datetime import date, timedelta
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from membership.filters import MembershipFilter
from membership.models import Membership
from membership.serializers import (
    MembershipCreateSerializer,
    MembershipReadSerializer,
)
from payments.models import Payment


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = MembershipFilter

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Membership.objects.all()
        return Membership.objects.filter(member=user)

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
                status=Payment.StatusChoices.PENDING,
                type=Payment.TypeChoices.MEMBERSHIP_PURCHASE,
                membership_id=membership.id,
                money_to_pay=membership.price_at_purchase
            )
