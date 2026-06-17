import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from membership.models import Membership
from payments.models import Payment
from payments.serializers.payment_create_serializer import PaymentCreateSerializer
from payments.services.stripe_service import StripeService

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Безопасно достаем membership (если не найден — вернет 404 для клиента)
        membership = get_object_or_404(
            Membership,
            id=serializer.validated_data["membership_id"]
        )

        # 1. Создаем платеж со статусом PENDING
        payment = Payment.objects.create(
            membership=membership,
            type=serializer.validated_data["payment_type"],
            money_to_pay=membership.price_at_purchase,  # Или твоё поле стоимости
            status=Payment.Status.PENDING
        )

        try:
            # 2. Генерируем сессию. Сервис должен обновить у себя внутри
            # поля payment.session_id и payment.session_url и вызвать payment.save()
            session = StripeService.create_checkout_session(payment, request)

            return Response(
                {"checkout_url": session.url},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            # Если Stripe API упал, удаляем «черновик» платежа, чтобы не копить мусор
            payment.delete()
            return Response(
                {"error": f"Stripe session creation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentSuccessView(APIView):
    """
    GET: success/ - Проверяет статус платежа в нашей БД
    """

    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"message": "Payment completed. Waiting for webhook confirmation."},
                status=status.HTTP_200_OK
            )

        # Пытаемся найти платеж по session_id, который Stripe прикрепит к редиректу
        payment = get_object_or_404(Payment, session_id=session_id)

        return Response(
            {
                "payment_id": payment.id,
                "status": payment.status,
                "message": "Payment verified successfully!" if payment.status == Payment.Status.PAID else "Payment is processing."
            },
            status=status.HTTP_200_OK
        )


class PaymentCancelView(APIView):
    """
    GET: cancel/ - Сообщение о приостановке платежа
    """

    def get(self, request):
        return Response(
            {"message": "Payment paused or cancelled. You can complete it later."},
            status=status.HTTP_200_OK
        )


class StripeWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            # Невалидный payload
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            # Невалидная подпись (кто-то чужой шлет запрос)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Главный кейс — успешная оплата checkout
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            # Извлекаем ID платежа из метаданных сессии
            payment_id = session.get("metadata", {}).get("payment_id")

            if not payment_id:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            try:
                payment = Payment.objects.get(id=payment_id)
            except Payment.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)

            # Если платеж еще не отмечен как оплаченный (например, SuccessView не успел этого сделать)
            if payment.status != Payment.Status.PAID:
                payment.status = Payment.Status.PAID
                payment.save(update_fields=["status"])

                # 🔔 ВОТ ЗДЕСЬ идеальное место, чтобы вызвать Celery таску
                # для активации абонемента или отправки сообщения в Телеграм!

        return Response(status=status.HTTP_200_OK)
