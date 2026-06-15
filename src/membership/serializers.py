from datetime import date
from rest_framework import serializers
from membership.models import Membership
from plans.models import MembershipPlan


class MembershipPlanShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipPlan
        fields = ["id", "name", "tier", "price"]


class MembershipReadSerializer(serializers.ModelSerializer):
    plan = MembershipPlanShortSerializer(read_only=True)
    member = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Membership
        fields = [
            "id", "member", "plan", "start_date", "end_date",
            "status", "auto_renew", "price_at_purchase", "frozen_from", "frozen_to"
        ]


class MembershipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ["id", "plan", "auto_renew"]

    def validate(self, attrs):
        user = self.context["request"].user
        active_or_pending_exists = Membership.objects.filter(
            member=user,
            status__in=[Membership.Status.ACTIVE, Membership.Status.FROZEN, Membership.Status.PENDING]
        ).exists()

        if active_or_pending_exists:
            raise serializers.ValidationError(
                "You already have an active, frozen, or pending membership payment."
            )
        return attrs
