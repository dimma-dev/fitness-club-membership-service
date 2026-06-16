from rest_framework import serializers

from membership.models import Membership
from payments.models import Payment


class PaymentCreateSerializer(serializers.Serializer):
    membership_id = serializers.IntegerField()
    payment_type = serializers.ChoiceField(
        choices=Payment.Type.choices
    )

    def validate_membership_id(self, value):
        try:
            Membership.objects.get(id=value)
        except Membership.DoesNotExist:
            raise serializers.ValidationError(
                "Membership does not exist."
            )

        return value
