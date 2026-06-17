from django.urls import path
from payments.views import (
    CreateCheckoutSessionView,
    PaymentSuccessView,
    PaymentCancelView,
    StripeWebhookView,
)

urlpatterns = [
    path("", CreateCheckoutSessionView.as_view(), name="payment-create"),
    path("success/", PaymentSuccessView.as_view(), name="payment-success"),
    path("cancel/", PaymentCancelView.as_view(), name="payment-cancel"),
    path("webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
