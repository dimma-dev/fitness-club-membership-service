from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "membership",
        "status",
        "type",
        "money_to_pay",
        "created_at"
    )

    list_filter = ("status", "type", "created_at")

    search_fields = ("session_id", "membership__id")

    readonly_fields = ("session_id", "session_url", "created_at")

    fieldsets = (
        ("General Information", {
            "fields": ("membership", "status", "type", "money_to_pay")
        }),
        ("Stripe Technical Data", {
            "fields": ("session_id", "session_url"),
            "description": "Technical session data synchronized with Stripe API."
        }),
        ("Timestamps", {
            "fields": ("created_at",),
        }),
    )

    def has_add_permission(self, request):
        return False
