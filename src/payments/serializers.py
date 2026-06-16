from rest_framework import serializers
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "membership",
            "status",
            "type",
            "money_to_pay",
            "session_url",
            "session_id",
        ]
        read_only_fields = [
            "status",
            "session_url",
            "session_id",
        ]
