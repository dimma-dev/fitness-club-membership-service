import stripe
from django.conf import settings
from django.urls import reverse
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:

    @staticmethod
    def create_checkout_session(membership, payment_type, amount, request, new_plan_id=None):
        """
        Creates a Payment record in the DB and a corresponding Stripe Checkout Session.
        Converts the amount to cents for Stripe and populates metadata.
        """
        payment = Payment.objects.create(
            membership=membership,
            type=payment_type,
            money_to_pay=amount,
            status=Payment.Status.PENDING
        )

        success_url = request.build_absolute_uri(
            reverse("payment-success")
        ) + "?session_id={CHECKOUT_SESSION_ID}"

        cancel_url = request.build_absolute_uri(reverse("payment-cancel"))

        metadata = {
            "payment_id": payment.id
        }
        if new_plan_id:
            metadata["new_plan_id"] = new_plan_id

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Payment #{payment.id} - {payment.get_type_display()}",
                    },
                    "unit_amount": int(payment.money_to_pay * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )

        payment.session_id = session.id
        payment.session_url = session.url
        payment.save(update_fields=["session_id", "session_url"])

        return payment
