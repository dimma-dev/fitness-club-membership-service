from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    # Делаем эти поля только для чтения (Read Only), потому что их генерирует
    # исключительно Stripe на бэкенде. Пользователь не должен передавать их в POST-запросе.
    status = serializers.CharField(read_only=True)
    session_url = serializers.URLField(read_only=True)
    session_id = serializers.CharField(read_only=True)

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
            "created_at",
        ]

    def validate_money_to_pay(self, value):
        """
        Валидация суммы: сумма платежа не может быть нулевой или отрицательной.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Сумма к оплате должна быть больше нуля."
            )
        return value