import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentSuccessView(APIView):
    def get(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"error": "session_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == "paid":
            payment = Payment.objects.get(session_id=session_id)
            payment.status = Payment.Status.PAID
            payment.save()
            return Response({"message": "Payment successful!"})

        return Response(
            {"message": "Payment not completed yet"},
            status=status.HTTP_400_BAD_REQUEST
        )


class PaymentCancelView(APIView):
    def get(self, request):
        return Response({
            "message": "Payment cancelled. You can complete it later. Session is available for 24 hours."
        })
