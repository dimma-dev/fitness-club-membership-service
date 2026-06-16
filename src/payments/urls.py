from django.urls import path
from payments.views import (
    CreateCheckoutSessionView,
    PaymentSuccessView,
    PaymentCancelView,
    StripeWebhookView,
)

urlpatterns = [
    path("", CreateCheckoutSessionView.as_view(), name="payment-create"),
    path("success/", PaymentSuccessView.as_view()),
    path("cancel/", PaymentCancelView.as_view()),
    path("webhook/", StripeWebhookView.as_view()),
]
