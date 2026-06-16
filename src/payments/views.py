import stripe

from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from membership.models import Membership
from payments.models import Payment
from payments.serializers.payment_create_serializer import (
    PaymentCreateSerializer,
)
from payments.services.stripe_service import StripeService


stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        membership = Membership.objects.get(
            id=serializer.validated_data["membership_id"]
        )

        payment = Payment.objects.create(
            membership=membership,
            type=serializer.validated_data["payment_type"],
            money_to_pay=membership.price_at_purchase,
        )

        session = StripeService.create_checkout_session(
            payment,
            request
        )

        return Response(
            {
                "checkout_url": session.url
            },
            status=status.HTTP_201_CREATED
        )


class PaymentSuccessView(APIView):

    def get(self, request):
        return Response(
            {
                "message": (
                    "Payment completed. "
                    "Waiting for webhook confirmation."
                )
            },
            status=status.HTTP_200_OK
        )


class PaymentCancelView(APIView):

    def get(self, request):
        return Response(
            {
                "message": "Payment cancelled."
            },
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
        except Exception:
            return Response(status=400)

        # Главный кейс — успешная оплата checkout
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            payment_id = session["metadata"]["payment_id"]

            try:
                payment = Payment.objects.get(id=payment_id)
            except Payment.DoesNotExist:
                return Response(status=404)

            payment.status = Payment.Status.PAID
            payment.save(update_fields=["status"])

        return Response(status=200)
