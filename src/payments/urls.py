from django.urls import path
from payments.views import PaymentSuccessView, PaymentCancelView

urlpatterns = [
    path("success/", PaymentSuccessView.as_view(), name="payment-success"),
    path("cancel/", PaymentCancelView.as_view(), name="payment-cancel"),
]
