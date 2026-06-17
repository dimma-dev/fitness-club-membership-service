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
        # 1. Create a "PENDING" payment record in our local database first
        payment = Payment.objects.create(
            membership=membership,
            type=payment_type,
            money_to_pay=amount,
            status=Payment.Status.PENDING
        )

        # 2. Build absolute URLs for redirection back to our Django views
        # Stripe automatically replaces {CHECKOUT_SESSION_ID} with the actual session ID upon redirect
        success_url = request.build_absolute_uri(
            reverse("payment-success")
        ) + "?session_id={CHECKOUT_SESSION_ID}"

        cancel_url = request.build_absolute_uri(reverse("payment-cancel"))

        # 3. Prepare metadata for the Stripe Webhook to consume later
        metadata = {
            "payment_id": payment.id
        }
        if new_plan_id:
            metadata["new_plan_id"] = new_plan_id

        # 4. Interact with Stripe API
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Payment #{payment.id} - {payment.get_type_display()}",
                    },
                    # Stripe expects an integer in cents (e.g., $25.00 -> 2500)
                    "unit_amount": int(payment.money_to_pay * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )

        # 5. Save the generated Stripe credentials back to our Payment model
        payment.session_id = session.id
        payment.session_url = session.url
        payment.save(update_fields=["session_id", "session_url"])

        return payment