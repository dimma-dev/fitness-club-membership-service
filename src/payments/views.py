import stripe
import logging
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from membership.models import Membership
from payments.models import Payment
from membership.tasks import notify_payment_success
from payments.serializers import PaymentSerializer
from payments.services.stripe_service import StripeService

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        membership = get_object_or_404(
            Membership,
            id=serializer.validated_data["membership_id"]
        )

        payment = Payment.objects.create(
            membership=membership,
            type=serializer.validated_data["payment_type"],
            money_to_pay=membership.price_at_purchase,
            status=Payment.Status.PENDING
        )

        try:
            session = StripeService.create_checkout_session(payment, request)
            return Response(
                {"checkout_url": session.url},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            payment.delete()
            return Response(
                {"error": f"Stripe session creation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentSuccessView(APIView):

    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"message": "Payment completed. Waiting for webhook confirmation."},
                status=status.HTTP_200_OK
            )

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
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Received Stripe event: {event['type']}")

        if event["type"] != "checkout.session.completed":
            return Response(status=status.HTTP_200_OK)

        payment_id = self._extract_payment_id(event["data"]["object"])
        if not payment_id:
            return Response(
                {"detail": "Invalid or missing payment_id"},
                status=status.HTTP_400_BAD_REQUEST if payment_id is False else status.HTTP_200_OK
            )

        return self._process_payment_completion(payment_id)

    def _extract_payment_id(self, session):
        metadata = getattr(session, "metadata", None)
        raw_payment_id = getattr(metadata, "payment_id", None) if metadata else None

        if not raw_payment_id:
            logger.warning("Webhook received, but no payment_id in metadata.")
            return None

        try:
            return int(raw_payment_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid payment_id format in metadata: {raw_payment_id}")
            return False

    def _process_payment_completion(self, payment_id):
        try:
            payment = Payment.objects.select_related("membership").get(id=payment_id)
        except Payment.DoesNotExist:
            logger.error(f"Payment with ID {payment_id} not found in database")
            return Response(status=status.HTTP_404_NOT_FOUND)

        if payment.status == Payment.Status.PAID:
            logger.info(f"Payment {payment.id} is already marked as PAID")
            return Response(status=status.HTTP_200_OK)

        with transaction.atomic():
            payment.status = Payment.Status.PAID
            payment.save(update_fields=["status"])
            logger.info(f"Payment {payment.id} status updated to PAID.")

            membership = payment.membership
            if membership and membership.status == Membership.Status.PENDING:
                membership.status = Membership.Status.ACTIVE
                membership.save(update_fields=["status"])
                logger.info(f"Membership {membership.id} status updated to ACTIVE.")

        notify_payment_success.delay(payment.id)
        return Response(status=status.HTTP_200_OK)
