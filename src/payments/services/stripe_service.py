import stripe

from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeService:

    @staticmethod
    def create_checkout_session(payment, request):
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(
                            payment.money_to_pay * 100
                        ),
                        "product_data": {
                            "name": (
                                f"{payment.type}"
                            )
                        },
                    },
                    "quantity": 1,
                }
            ],
            metadata={
                "payment_id": payment.id
            },
            success_url=request.build_absolute_uri(
                "/api/payments/success/"
            ),
            cancel_url=request.build_absolute_uri(
                "/api/payments/cancel/"
            ),
        )

        payment.session_id = session.id
        payment.session_url = session.url

        payment.save(
            update_fields=[
                "session_id",
                "session_url"
            ]
        )

        return session
