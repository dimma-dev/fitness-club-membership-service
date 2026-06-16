import stripe
from datetime import date
from django.conf import settings
from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_session(membership, payment_type, amount, request):
    amount_cents = int(amount * 100)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": amount_cents,
                "product_data": {
                    "name": f"{payment_type} - {membership.plan.name}",
                },
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=(
            request.build_absolute_uri(
                "/api/payments/success/?session_id={CHECKOUT_SESSION_ID}"
            )
        ),
        cancel_url=request.build_absolute_uri("/api/payments/cancel/"),
    )

    payment = Payment.objects.create(
        membership=membership,
        type=payment_type,
        money_to_pay=amount,
        session_url=session.url,
        session_id=session.id,
    )

    return payment
